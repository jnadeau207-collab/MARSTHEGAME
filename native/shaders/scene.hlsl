cbuffer SceneConstants : register(b0)
{
    row_major float4x4 world;
    row_major float4x4 worldViewProjection;
    float4 lightDirection;
    float4 tint;
    float4 materialParameters;
    float4 materialLayerMask;
};

Texture2DArray<float4> baseColorTexture : register(t0);
Texture2DArray<float4> normalTexture : register(t1);
Texture2DArray<float4> surfaceTexture : register(t2);
SamplerState materialSampler : register(s0);

struct VertexInput
{
    float3 position : POSITION;
    float3 normal : NORMAL;
    float3 color : COLOR;
};

struct PixelInput
{
    float4 position : SV_POSITION;
    float3 worldPosition : TEXCOORD0;
    float3 normal : NORMAL;
    float3 color : COLOR;
};

PixelInput VSMain(VertexInput input)
{
    PixelInput output;
    const float4 worldPosition = mul(float4(input.position, 1.0f), world);
    output.position = mul(float4(input.position, 1.0f), worldViewProjection);
    output.worldPosition = worldPosition.xyz;
    output.normal = normalize(mul(float4(input.normal, 0.0f), world).xyz);
    output.color = input.color * tint.rgb;
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

float4 PSMain(PixelInput input) : SV_TARGET
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

    const float roughness = saturate(generatedSurface.r * 0.72f + materialParameters.z * 0.28f);
    const float metallic = saturate(generatedSurface.g * 0.72f + materialParameters.w * 0.28f);
    const float authoredMask = saturate(generatedSurface.b * materialLayerMask.y);
    const float occlusion = saturate(generatedSurface.a);
    const float3 albedo = generatedBase.rgb * input.color;

    const float3 light = normalize(-lightDirection.xyz);
    const float3 viewDirection = normalize(float3(0.18f, 0.45f, -1.0f));
    const float3 halfVector = normalize(light + viewDirection);
    const float diffuse = saturate(dot(normal, light));
    const float skyFill = saturate(normal.y * 0.5f + 0.5f);
    const float horizon = saturate(normal.z * 0.18f + 0.82f);
    const float specularPower = lerp(72.0f, 4.0f, roughness);
    const float specular = pow(saturate(dot(normal, halfVector)), specularPower)
        * lerp(0.16f, 0.62f, metallic);
    const float3 specularColor = lerp(float3(0.04f, 0.04f, 0.04f), albedo, metallic);
    const float diffuseEnergy = lerp(1.0f, 0.34f, metallic);
    const float lighting = (0.13f + diffuse * 0.69f + skyFill * 0.12f + horizon * 0.06f)
        * lerp(0.78f, 1.0f, occlusion);
    const float maskAccent = lerp(0.94f, 1.12f, authoredMask);
    const float3 color = albedo * lighting * diffuseEnergy * maskAccent
        + specularColor * specular;
    return float4(color, 1.0f);
}
