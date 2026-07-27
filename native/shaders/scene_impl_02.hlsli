    float3 maximumCurrent = current;
    const float2 offsets[4] = {
        float2(texel.x, 0.0f),
        float2(-texel.x, 0.0f),
        float2(0.0f, texel.y),
        float2(0.0f, -texel.y)
    };
    [unroll]
    for (uint index = 0; index < 4; ++index)
    {
        const float3 neighbour = hdrTexture.SampleLevel(linearClampSampler, input.uv + offsets[index], 0.0f).rgb;
        minimumCurrent = min(minimumCurrent, neighbour);
        maximumCurrent = max(maximumCurrent, neighbour);
    }
    history = clamp(history, minimumCurrent, maximumCurrent);
    const float motion = saturate(length(cameraMotionJitter.xy) * 180.0f);
    const float historyWeight = skyZenithHistory.w * (1.0f - motion * 0.65f);
    return float4(lerp(current, history, historyWeight), 1.0f);
}

float3 AcesToneMap(float3 color)
{
    const float3 a = color * (2.51f * color + 0.03f);
    const float3 b = color * (2.43f * color + 0.59f) + 0.14f;
    return saturate(a / b);
}

float LinearizeDepth(float depth)
{
    const float nearPlane = focusParameters.z;
    const float farPlane = focusParameters.w;
    return nearPlane * farPlane / max(farPlane - depth * (farPlane - nearPlane), 0.0001f);
}

float3 SampleResolved(float2 uv)
{
    return SampleHistory(uv, postParameters.w).rgb;
}

float3 EvaluateProceduralSky(float2 uv, float aspect)
{
    const float2 ndc = float2(uv.x * 2.0f - 1.0f, 1.0f - uv.y * 2.0f);
    const float3 forward = normalize(cross(cameraRight.xyz, cameraUp.xyz));
    const float3 ray = normalize(
        forward
        + cameraRight.xyz * ndc.x * aspect * 0.5543f
        + cameraUp.xyz * ndc.y * 0.5543f);
    const float height = saturate(ray.y * 0.5f + 0.5f);
    const float horizonBand = exp(-abs(ray.y) * 7.5f);
    const float3 generatedSky = SampleGeneratedEnvironment(ray);
    const float3 zenith = skyZenithHistory.rgb * 1.8f + float3(0.008f, 0.012f, 0.028f);
    const float3 horizon = horizonColorBloom.rgb * 2.4f + float3(0.12f, 0.028f, 0.012f);
    float3 sky = lerp(horizon, zenith, pow(height, 0.72f));
    sky = lerp(sky, generatedSky * 1.35f, 0.46f);
    sky += horizon * horizonBand * 0.35f;

    const float3 sunDirection = normalize(-sunDirectionExposure.xyz);
    const float sunAlignment = saturate(dot(ray, sunDirection));
    const float sunDisc = pow(sunAlignment, 1800.0f) * 18.0f;
    const float sunHalo = pow(sunAlignment, 28.0f) * 0.55f;
    sky += sunColorIntensity.rgb * (sunDisc + sunHalo);

    const float dustVariation = Hash11(floor(uv.x * 96.0f) + floor(uv.y * 54.0f) * 131.0f);
    sky *= 0.985f + dustVariation * 0.03f;
    return max(sky, 0.0f);
}

float4 FinalPS(FullscreenOutput input) : SV_TARGET
{
    uint width = 0;
    uint height = 0;
    sceneDepthTexture.GetDimensions(width, height);
    const float2 texel = 1.0f / float2(width, height);
    const float depth = sceneDepthTexture.SampleLevel(linearClampSampler, input.uv, 0.0f);
    const bool skyPixel = depth >= 0.99999f;
    const float viewDepth = LinearizeDepth(depth);
    const float focusBlur = skyPixel ? 0.0f : saturate(abs(viewDepth - focusParameters.x) / focusParameters.y);

    float3 color = skyPixel
        ? EvaluateProceduralSky(input.uv, float(width) / float(height))
        : SampleResolved(input.uv);
    if (!skyPixel)
    {
        const float2 motionVector = cameraMotionJitter.xy * postParameters.x;
        [unroll]
        for (int sampleIndex = -2; sampleIndex <= 2; ++sampleIndex)
        {
            color += SampleResolved(input.uv + motionVector * (float(sampleIndex) * 0.25f));
        }
        color /= 6.0f;
    }

    const float2 bloomOffsets[8] = {
        float2(1.0f, 0.0f), float2(-1.0f, 0.0f),
        float2(0.0f, 1.0f), float2(0.0f, -1.0f),
        float2(0.707f, 0.707f), float2(-0.707f, 0.707f),
        float2(0.707f, -0.707f), float2(-0.707f, -0.707f)
    };
    if (!skyPixel)
    {
        float3 bloom = 0.0f;
        [unroll]
        for (uint bloomIndex = 0; bloomIndex < 8; ++bloomIndex)
        {
            const float3 sampleColor = SampleResolved(input.uv + bloomOffsets[bloomIndex] * texel * 4.0f);
            const float luminance = dot(sampleColor, float3(0.2126f, 0.7152f, 0.0722f));
            bloom += sampleColor * saturate(luminance - horizonColorBloom.w);
        }
        color += bloom * 0.095f;
    }

    if (focusBlur > 0.02f)
    {
        float3 defocused = 0.0f;
        [unroll]
        for (uint blurIndex = 0; blurIndex < 8; ++blurIndex)
        {
            defocused += SampleResolved(input.uv + bloomOffsets[blurIndex] * texel * (1.5f + focusBlur * 5.0f));
        }
        color = lerp(color, defocused / 8.0f, focusBlur * 0.52f);
    }

    color = AcesToneMap(color * sunDirectionExposure.w);
    const float2 centered = input.uv * 2.0f - 1.0f;
    const float vignette = saturate(1.0f - dot(centered, centered) * postParameters.y);
    const float cornerFade = smoothstep(1.27f, 1.41f, length(centered));
    const float cinematicVignette = lerp(1.0f, 0.001f, cornerFade)
        * lerp(0.82f, 1.0f, vignette);
    const float displayLuminance = dot(color, float3(0.2126f, 0.7152f, 0.0722f));
    const float grainSeed = dot(floor(input.position.xy), float2(12.9898f, 78.233f))
        + floor(cameraPositionTime.w * 24.0f) * 19.19f;
    const float grain = (frac(sin(grainSeed) * 43758.5453f) - 0.5f)
        * 0.0035f * saturate(displayLuminance * 4.0f);
    color = saturate(color * cinematicVignette + grain);

    const float2 subtitleMinimum = float2(0.18f, 0.82f);
    const float2 subtitleMaximum = float2(0.82f, 0.94f);
    if (all(input.uv >= subtitleMinimum) && all(input.uv <= subtitleMaximum))
    {
        const float2 subtitleUv = (input.uv - subtitleMinimum) / (subtitleMaximum - subtitleMinimum);
        const float subtitleLayer = fogColorDensity.g > 0.10f ? 1.0f : 0.0f;
        const float4 subtitle = subtitleTexture.SampleLevel(
            linearClampSampler,
            float3(subtitleUv, subtitleLayer),
            0.0f);
        const float3 subtitleLinear = pow(max(subtitle.rgb, 0.0f), 2.2f);
        color = lerp(color, subtitleLinear, subtitle.a);
    }

    color = pow(saturate(color), 1.0f / 2.2f);
    return float4(color, 1.0f);
}
