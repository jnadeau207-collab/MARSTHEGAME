cbuffer ObjectConstants : register(b0)
{
    row_major float4x4 world;
    row_major float4x4 worldInverseTranspose;
    row_major float4x4 worldViewProjection;
    row_major float4x4 previousWorldViewProjection;
    row_major float4x4 worldLightViewProjection;
    float4 tint;
    float4 materialParameters;
    float4 materialLayerMask;
};

cbuffer FrameConstants : register(b1)
{
    row_major float4x4 viewProjection;
    row_major float4x4 previousViewProjection;
    row_major float4x4 lightViewProjection;
    float4 cameraPositionTime;
    float4 sunDirectionExposure;
    float4 sunColorIntensity;
    float4 fogColorDensity;
    float4 skyZenithHistory;
    float4 horizonColorBloom;
    float4 postParameters;
    float4 focusParameters;
    float4 cameraMotionJitter;
    float4 particleEmitterCount;
    float4 cameraRight;
    float4 cameraUp;
    float4 localLightPositionRadius[4];
    float4 localLightColorIntensity[4];
};

Texture2DArray<float4> baseColorTexture : register(t0);
Texture2DArray<float4> normalTexture : register(t1);
Texture2DArray<float4> surfaceTexture : register(t2);
Texture2D<float> shadowTexture : register(t3);
Texture2D<float4> hdrTexture : register(t4);
Texture2D<float4> historyTexture0 : register(t5);
Texture2D<float4> historyTexture1 : register(t6);
Texture2D<float> sceneDepthTexture : register(t7);
SamplerState materialSampler : register(s0);
SamplerComparisonState shadowSampler : register(s1);
SamplerState linearClampSampler : register(s2);

static const float PI = 3.14159265359f;

struct VertexInput
{
    float3 position : POSITION;
    float3 normal : NORMAL;
    float3 color : COLOR;
};

struct ScenePixelInput
{
    float4 position : SV_POSITION;
    float3 worldPosition : TEXCOORD0;
    float3 normal : NORMAL;
    float3 color : COLOR;
    float4 currentClip : TEXCOORD1;
    float4 previousClip : TEXCOORD2;
    float4 lightClip : TEXCOORD3;
    float emissive : TEXCOORD4;
};

float4 ShadowVS(VertexInput input) : SV_POSITION
{
    return mul(float4(input.position, 1.0f), worldLightViewProjection);
}

ScenePixelInput SceneVS(VertexInput input)
{
    ScenePixelInput output;
    const float4 localPosition = float4(input.position, 1.0f);
    const float4 worldPosition = mul(localPosition, world);
    output.position = mul(localPosition, worldViewProjection);
    output.worldPosition = worldPosition.xyz;
    output.normal = normalize(mul(float4(input.normal, 0.0f), worldInverseTranspose).xyz);
    output.color = input.color * tint.rgb;
    output.currentClip = output.position;
    output.previousClip = mul(localPosition, previousWorldViewProjection);
    output.lightClip = mul(localPosition, worldLightViewProjection);
    output.emissive = max(tint.a - 1.0f, 0.0f);
    return output;
}

float3 TriplanarWeights(float3 normal)
{
    float3 weights = pow(abs(normal), 4.0f);
    return weights / max(weights.x + weights.y + weights.z, 0.0001f);
}

float4 SampleBaseColor(float3 position, float3 weights, float layer, float scale)
{
    const float2 uvX = position.zy * scale;
    const float2 uvY = position.xz * scale;
    const float2 uvZ = position.xy * scale;
    return baseColorTexture.Sample(materialSampler, float3(uvX, layer)) * weights.x
        + baseColorTexture.Sample(materialSampler, float3(uvY, layer)) * weights.y
        + baseColorTexture.Sample(materialSampler, float3(uvZ, layer)) * weights.z;
}

float4 SampleSurface(float3 position, float3 weights, float layer, float scale)
{
    const float2 uvX = position.zy * scale;
    const float2 uvY = position.xz * scale;
    const float2 uvZ = position.xy * scale;
    return surfaceTexture.Sample(materialSampler, float3(uvX, layer)) * weights.x
        + surfaceTexture.Sample(materialSampler, float3(uvY, layer)) * weights.y
        + surfaceTexture.Sample(materialSampler, float3(uvZ, layer)) * weights.z;
}

float3 SampleWorldNormal(
    float3 position,
    float3 geometricNormal,
    float3 weights,
    float layer,
    float scale,
    float strength)
{
    const float2 uvX = position.zy * scale;
    const float2 uvY = position.xz * scale;
    const float2 uvZ = position.xy * scale;
    const float3 tangentX = normalTexture.Sample(materialSampler, float3(uvX, layer)).xyz * 2.0f - 1.0f;
    const float3 tangentY = normalTexture.Sample(materialSampler, float3(uvY, layer)).xyz * 2.0f - 1.0f;
    const float3 tangentZ = normalTexture.Sample(materialSampler, float3(uvZ, layer)).xyz * 2.0f - 1.0f;
    const float signX = geometricNormal.x < 0.0f ? -1.0f : 1.0f;
    const float signY = geometricNormal.y < 0.0f ? -1.0f : 1.0f;
    const float signZ = geometricNormal.z < 0.0f ? -1.0f : 1.0f;
    const float3 worldX = normalize(float3(tangentX.z * signX, tangentX.y, tangentX.x));
    const float3 worldY = normalize(float3(tangentY.x, tangentY.z * signY, tangentY.y));
    const float3 worldZ = normalize(float3(tangentZ.x, tangentZ.y, tangentZ.z * signZ));
    const float3 detailed = normalize(worldX * weights.x + worldY * weights.y + worldZ * weights.z);
    return normalize(lerp(geometricNormal, detailed, saturate(strength)));
}

float DistributionGGX(float3 normal, float3 halfVector, float roughness)
{
    const float a = roughness * roughness;
    const float a2 = a * a;
    const float nDotH = saturate(dot(normal, halfVector));
    const float denominator = nDotH * nDotH * (a2 - 1.0f) + 1.0f;
    return a2 / max(PI * denominator * denominator, 0.0001f);
}

float GeometrySchlickGGX(float nDotDirection, float roughness)
{
    const float r = roughness + 1.0f;
    const float k = r * r * 0.125f;
    return nDotDirection / max(nDotDirection * (1.0f - k) + k, 0.0001f);
}

float GeometrySmith(float3 normal, float3 viewDirection, float3 lightDirection, float roughness)
{
    return GeometrySchlickGGX(saturate(dot(normal, viewDirection)), roughness)
        * GeometrySchlickGGX(saturate(dot(normal, lightDirection)), roughness);
}

float3 FresnelSchlick(float cosine, float3 f0)
{
    return f0 + (1.0f - f0) * pow(saturate(1.0f - cosine), 5.0f);
}

float SampleShadow(float4 lightClip)
{
    const float3 projected = lightClip.xyz / max(lightClip.w, 0.0001f);
    const float2 uv = float2(projected.x * 0.5f + 0.5f, -projected.y * 0.5f + 0.5f);
    if (uv.x <= 0.0f || uv.x >= 1.0f || uv.y <= 0.0f || uv.y >= 1.0f || projected.z <= 0.0f || projected.z >= 1.0f)
    {
        return 1.0f;
    }
    uint shadowWidth = 0;
    uint shadowHeight = 0;
    shadowTexture.GetDimensions(shadowWidth, shadowHeight);
    const float2 texel = 1.0f / float2(shadowWidth, shadowHeight);
    float visibility = 0.0f;
    [unroll]
    for (int y = -1; y <= 1; ++y)
    {
        [unroll]
        for (int x = -1; x <= 1; ++x)
