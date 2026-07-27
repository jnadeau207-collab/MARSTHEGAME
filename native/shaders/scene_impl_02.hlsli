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

float4 FinalPS(FullscreenOutput input) : SV_TARGET
{
    uint width = 0;
    uint height = 0;
    sceneDepthTexture.GetDimensions(width, height);
    const float2 texel = 1.0f / float2(width, height);
    const float depth = sceneDepthTexture.SampleLevel(linearClampSampler, input.uv, 0.0f);
    const float viewDepth = LinearizeDepth(depth);
    const float focusBlur = saturate(abs(viewDepth - focusParameters.x) / focusParameters.y);

    float3 color = SampleResolved(input.uv);
    const float2 motionVector = cameraMotionJitter.xy * postParameters.x;
    [unroll]
    for (int sampleIndex = -2; sampleIndex <= 2; ++sampleIndex)
    {
        color += SampleResolved(input.uv + motionVector * (float(sampleIndex) * 0.25f));
    }
    color /= 6.0f;

    float3 bloom = 0.0f;
    const float2 bloomOffsets[8] = {
        float2(1.0f, 0.0f), float2(-1.0f, 0.0f),
        float2(0.0f, 1.0f), float2(0.0f, -1.0f),
        float2(0.707f, 0.707f), float2(-0.707f, 0.707f),
        float2(0.707f, -0.707f), float2(-0.707f, -0.707f)
    };
    [unroll]
    for (uint bloomIndex = 0; bloomIndex < 8; ++bloomIndex)
    {
        const float3 sampleColor = SampleResolved(input.uv + bloomOffsets[bloomIndex] * texel * 4.0f);
        const float luminance = dot(sampleColor, float3(0.2126f, 0.7152f, 0.0722f));
        bloom += sampleColor * saturate(luminance - horizonColorBloom.w);
    }
    color += bloom * 0.075f;

    if (focusBlur > 0.02f)
    {
        float3 defocused = 0.0f;
        [unroll]
        for (uint blurIndex = 0; blurIndex < 8; ++blurIndex)
        {
            defocused += SampleResolved(input.uv + bloomOffsets[blurIndex] * texel * (2.0f + focusBlur * 7.0f));
        }
        color = lerp(color, defocused / 8.0f, focusBlur * 0.72f);
    }

    color = AcesToneMap(color * sunDirectionExposure.w);
    const float2 centered = input.uv * 2.0f - 1.0f;
    const float vignette = saturate(1.0f - dot(centered, centered) * postParameters.y);
    const float grain = (Hash11(input.position.x + input.position.y * 4096.0f + cameraPositionTime.w * 73.0f) - 0.5f) * 0.012f;
    color = pow(saturate(color * lerp(0.78f, 1.0f, vignette) + grain), 1.0f / 2.2f);
    return float4(color, 1.0f);
}
