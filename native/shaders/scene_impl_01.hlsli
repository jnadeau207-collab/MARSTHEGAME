        {
            visibility += shadowTexture.SampleCmpLevelZero(
                shadowSampler,
                uv + float2(x, y) * texel,
                projected.z - 0.0016f);
        }
    }
    return visibility / 9.0f;
}

float3 EvaluateLight(
    float3 normal,
    float3 viewDirection,
    float3 lightDirection,
    float3 radiance,
    float3 albedo,
    float roughness,
    float metallic,
    float shadow)
{
    const float3 halfVector = normalize(viewDirection + lightDirection);
    const float nDotL = saturate(dot(normal, lightDirection));
    const float nDotV = saturate(dot(normal, viewDirection));
    const float3 f0 = lerp(float3(0.04f, 0.04f, 0.04f), albedo, metallic);
    const float3 fresnel = FresnelSchlick(saturate(dot(halfVector, viewDirection)), f0);
    const float distribution = DistributionGGX(normal, halfVector, roughness);
    const float geometry = GeometrySmith(normal, viewDirection, lightDirection, roughness);
    const float3 specular = distribution * geometry * fresnel / max(4.0f * nDotV * nDotL, 0.001f);
    const float3 diffuse = (1.0f - fresnel) * (1.0f - metallic) * albedo / PI;
    return (diffuse + specular) * radiance * nDotL * shadow;
}

float4 ScenePS(ScenePixelInput input) : SV_TARGET
{
    const float3 geometricNormal = normalize(input.normal);
    const float3 weights = TriplanarWeights(geometricNormal);
    const float layer = materialLayerMask.x;
    const float scale = materialParameters.x;
    const float4 generatedBase = SampleBaseColor(input.worldPosition, weights, layer, scale);
    const float4 generatedSurface = SampleSurface(input.worldPosition, weights, layer, scale);
    const float3 normal = SampleWorldNormal(
        input.worldPosition,
        geometricNormal,
        weights,
        layer,
        scale,
        materialParameters.y);
    const float roughness = clamp(generatedSurface.r * 0.72f + materialParameters.z * 0.28f, 0.06f, 1.0f);
    const float metallic = saturate(generatedSurface.g * 0.72f + materialParameters.w * 0.28f);
    const float authoredMask = saturate(generatedSurface.b * materialLayerMask.y);
    const float occlusion = saturate(generatedSurface.a);
    const float3 albedo = max(generatedBase.rgb * input.color, 0.0f);
    const float3 viewDirection = normalize(cameraPositionTime.xyz - input.worldPosition);

    const float3 sunDirection = normalize(-sunDirectionExposure.xyz);
    const float sunShadow = SampleShadow(input.lightClip);
    float3 color = EvaluateLight(
        normal,
        viewDirection,
        sunDirection,
        sunColorIntensity.rgb * sunColorIntensity.w,
        albedo,
        roughness,
        metallic,
        sunShadow);

    [unroll]
    for (uint lightIndex = 0; lightIndex < 4; ++lightIndex)
    {
        const float3 toLight = localLightPositionRadius[lightIndex].xyz - input.worldPosition;
        const float distanceToLight = length(toLight);
        const float radius = max(localLightPositionRadius[lightIndex].w, 0.001f);
        const float attenuation = pow(saturate(1.0f - distanceToLight / radius), 2.0f);
        if (attenuation > 0.0f)
        {
            color += EvaluateLight(
                normal,
                viewDirection,
                toLight / max(distanceToLight, 0.001f),
                localLightColorIntensity[lightIndex].rgb
                    * localLightColorIntensity[lightIndex].w * attenuation,
                albedo,
                roughness,
                metallic,
                1.0f);
        }
    }

    const float skyAmount = saturate(normal.y * 0.5f + 0.5f);
    const float3 ambientSky = lerp(horizonColorBloom.rgb, skyZenithHistory.rgb, skyAmount);
    color += ambientSky * albedo * (0.08f + 0.17f * occlusion) * (1.0f - metallic * 0.65f);
    color += albedo * authoredMask * float3(0.20f, 0.055f, 0.012f);

    const float cameraDistance = length(cameraPositionTime.xyz - input.worldPosition);
    const float heightFog = exp(-max(input.worldPosition.y, 0.0f) * 0.04f);
    const float fogAmount = 1.0f - exp(-cameraDistance * fogColorDensity.w * heightFog);
    color = lerp(color, fogColorDensity.rgb, saturate(fogAmount));
    return float4(max(color, 0.0f), 1.0f);
}

struct ParticleOutput
{
    float4 position : SV_POSITION;
    float2 local : TEXCOORD0;
    float4 color : COLOR0;
};

float Hash11(float value)
{
    return frac(sin(value * 91.3458f) * 47453.5453f);
}

ParticleOutput ParticleVS(uint vertexId : SV_VertexID)
{
    ParticleOutput output;
    const uint particleIndex = vertexId / 3U;
    const uint cornerIndex = vertexId % 3U;
    const float count = max(particleEmitterCount.w, 1.0f);
    const float seed = float(particleIndex) + 1.0f;
    const float life = frac(cameraPositionTime.w * (0.055f + Hash11(seed) * 0.035f) + Hash11(seed * 2.7f));
    const float angle = Hash11(seed * 4.1f) * 6.2831853f + cameraPositionTime.w * 0.09f;
    const float radius = sqrt(Hash11(seed * 7.3f)) * (2.0f + 6.0f * life);
    const float3 center = particleEmitterCount.xyz + float3(
        cos(angle) * radius,
        0.18f + life * (2.6f + Hash11(seed * 11.0f) * 3.2f),
        sin(angle) * radius);
    const float2 triangle[3] = {
        float2(-0.75f, -0.55f),
        float2(0.75f, -0.55f),
        float2(0.0f, 0.90f)
    };
    const float size = lerp(0.045f, 0.20f, Hash11(seed * 13.0f)) * (0.45f + life * 0.55f);
    const float2 local = triangle[cornerIndex];
    const float3 worldPosition = center + cameraRight.xyz * local.x * size + cameraUp.xyz * local.y * size;
    output.position = mul(float4(worldPosition, 1.0f), viewProjection);
    output.local = local;
    const float alpha = saturate(sin(life * PI)) * (0.18f + 0.24f * Hash11(seed * 17.0f));
    output.color = float4(1.0f, 0.26f + Hash11(seed) * 0.15f, 0.065f, alpha / sqrt(count / 384.0f));
    return output;
}

float4 ParticlePS(ParticleOutput input) : SV_TARGET
{
    const float falloff = saturate(1.0f - dot(input.local, input.local));
    return float4(input.color.rgb * input.color.a * falloff * 3.0f, input.color.a * falloff);
}

struct FullscreenOutput
{
    float4 position : SV_POSITION;
    float2 uv : TEXCOORD0;
};

FullscreenOutput FullscreenVS(uint vertexId : SV_VertexID)
{
    FullscreenOutput output;
    const float2 position = vertexId == 0U ? float2(-1.0f, -1.0f)
        : (vertexId == 1U ? float2(-1.0f, 3.0f) : float2(3.0f, -1.0f));
    output.position = float4(position, 0.0f, 1.0f);
    output.uv = float2(position.x * 0.5f + 0.5f, 0.5f - position.y * 0.5f);
    return output;
}

float4 SampleHistory(float2 uv, float historyIndex)
{
    return historyIndex < 0.5f
        ? historyTexture0.SampleLevel(linearClampSampler, uv, 0.0f)
        : historyTexture1.SampleLevel(linearClampSampler, uv, 0.0f);
}

float4 TemporalPS(FullscreenOutput input) : SV_TARGET
{
    uint width = 0;
    uint height = 0;
    hdrTexture.GetDimensions(width, height);
    const float2 texel = 1.0f / float2(width, height);
    const float3 current = hdrTexture.SampleLevel(linearClampSampler, input.uv, 0.0f).rgb;
    const float2 historyUv = input.uv - cameraMotionJitter.xy;
    float3 history = SampleHistory(historyUv, postParameters.z).rgb;
    float3 minimumCurrent = current;
