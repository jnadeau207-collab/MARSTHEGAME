cbuffer SceneConstants : register(b0)
{
    row_major float4x4 world;
    row_major float4x4 worldViewProjection;
    float4 lightDirection;
    float4 tint;
};

struct VertexInput
{
    float3 position : POSITION;
    float3 normal : NORMAL;
    float3 color : COLOR;
};

struct PixelInput
{
    float4 position : SV_POSITION;
    float3 normal : NORMAL;
    float3 color : COLOR;
};

PixelInput VSMain(VertexInput input)
{
    PixelInput output;
    output.position = mul(float4(input.position, 1.0f), worldViewProjection);
    output.normal = normalize(mul(float4(input.normal, 0.0f), world).xyz);
    output.color = input.color * tint.rgb;
    return output;
}

float4 PSMain(PixelInput input) : SV_TARGET
{
    const float3 normal = normalize(input.normal);
    const float3 light = normalize(-lightDirection.xyz);
    const float diffuse = saturate(dot(normal, light));
    const float skyFill = saturate(normal.y * 0.5f + 0.5f);
    const float horizon = saturate(normal.z * 0.18f + 0.82f);
    const float lighting = 0.16f + diffuse * 0.68f + skyFill * 0.10f + horizon * 0.06f;
    return float4(input.color * lighting, 1.0f);
}
