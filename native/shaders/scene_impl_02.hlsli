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

    // Dusty early-morning Mars: neutral-cool upper sky and a restrained warm horizon.
    const float3 zenith = skyZenithHistory.rgb * 1.35f + float3(0.022f, 0.032f, 0.045f);
    const float3 horizon = horizonColorBloom.rgb * 1.55f + float3(0.24f, 0.115f, 0.055f);
    float3 sky = lerp(horizon, zenith, pow(height, 0.78f));
    sky = lerp(sky, generatedSky * 1.10f, 0.38f);
    sky += horizon * horizonBand * 0.20f;

    const float3 sunDirection = normalize(-sunDirectionExposure.xyz);
    const float sunAlignment = saturate(dot(ray, sunDirection));
    const float sunDisc = pow(sunAlignment, 1800.0f) * 12.0f;
    const float sunHalo = pow(sunAlignment, 32.0f) * 0.28f;
    sky += sunColorIntensity.rgb * (sunDisc + sunHalo);

    const float dustVariation = Hash11(floor(uv.x * 96.0f) + floor(uv.y * 54.0f) * 131.0f);
    sky *= 0.99f + dustVariation * 0.02f;
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
    if (!skyPixel && postParameters.x > 0.001f)
    {
        const float2 motionVector = cameraMotionJitter.xy * postParameters.x;
        float3 motionAccumulation = color;
        [unroll]
        for (int sampleIndex = -2; sampleIndex <= 2; ++sampleIndex)
        {
            motionAccumulation += SampleResolved(
                input.uv + motionVector * (float(sampleIndex) * 0.25f));
        }
        color = motionAccumulation / 6.0f;
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
            const float3 sampleColor = SampleResolved(
                input.uv + bloomOffsets[bloomIndex] * texel * 2.2f);
            const float luminance = dot(sampleColor, float3(0.2126f, 0.7152f, 0.0722f));
            bloom += sampleColor * saturate(luminance - horizonColorBloom.w);
        }
        color += bloom * 0.032f;
    }

    if (focusBlur > 0.08f)
    {
        float3 defocused = 0.0f;
        [unroll]
        for (uint blurIndex = 0; blurIndex < 8; ++blurIndex)
        {
            defocused += SampleResolved(
                input.uv + bloomOffsets[blurIndex] * texel * (1.0f + focusBlur * 2.0f));
        }
        color = lerp(color, defocused / 8.0f, focusBlur * 0.20f);
    }

    color = AcesToneMap(color * sunDirectionExposure.w);

    // The rejected candidate used a nearly black corner mask and animated film grain.
    // Recovery defaults preserve the authored frame and apply only a subtle optical falloff.
    const float2 centered = input.uv * 2.0f - 1.0f;
    const float radial = saturate(dot(centered, centered) * 0.50f);
    const float restrainedVignette = lerp(1.0f, 0.94f, radial);
    color = saturate(color * restrainedVignette);

    // Objective text is intentionally absent from this pass. The former giant pixel banner
    // is prohibited; professional scalable HUD rendering is a separate recovery tranche.

    color = pow(saturate(color), 1.0f / 2.2f);
    return float4(color, 1.0f);
}
