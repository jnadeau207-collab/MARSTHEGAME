}

void D3D12Renderer::CreatePipelines()
{
    const std::filesystem::path shader_directory = ExecutableDirectory() / L"shaders";
    const std::vector<std::uint8_t> shadow_vs = ReadBinaryFile(shader_directory / L"shadow.vs.dxil");
    const std::vector<std::uint8_t> scene_vs = ReadBinaryFile(shader_directory / L"scene.vs.dxil");
    const std::vector<std::uint8_t> scene_ps = ReadBinaryFile(shader_directory / L"scene.ps.dxil");
    const std::vector<std::uint8_t> particle_vs = ReadBinaryFile(shader_directory / L"particle.vs.dxil");
    const std::vector<std::uint8_t> particle_ps = ReadBinaryFile(shader_directory / L"particle.ps.dxil");
    const std::vector<std::uint8_t> fullscreen_vs = ReadBinaryFile(shader_directory / L"fullscreen.vs.dxil");
    const std::vector<std::uint8_t> temporal_ps = ReadBinaryFile(shader_directory / L"temporal.ps.dxil");
    const std::vector<std::uint8_t> final_ps = ReadBinaryFile(shader_directory / L"final.ps.dxil");

    D3D12_DESCRIPTOR_RANGE srv_range{};
    srv_range.RangeType = D3D12_DESCRIPTOR_RANGE_TYPE_SRV;
    srv_range.NumDescriptors = kSrvDescriptorCount;
    srv_range.BaseShaderRegister = 0;
    srv_range.RegisterSpace = 0;
    srv_range.OffsetInDescriptorsFromTableStart = D3D12_DESCRIPTOR_RANGE_OFFSET_APPEND;

    std::array<D3D12_ROOT_PARAMETER, 3> root_parameters{};
    root_parameters[0].ParameterType = D3D12_ROOT_PARAMETER_TYPE_CBV;
    root_parameters[0].Descriptor.ShaderRegister = 0;
    root_parameters[0].ShaderVisibility = D3D12_SHADER_VISIBILITY_ALL;
    root_parameters[1].ParameterType = D3D12_ROOT_PARAMETER_TYPE_CBV;
    root_parameters[1].Descriptor.ShaderRegister = 1;
    root_parameters[1].ShaderVisibility = D3D12_SHADER_VISIBILITY_ALL;
    root_parameters[2].ParameterType = D3D12_ROOT_PARAMETER_TYPE_DESCRIPTOR_TABLE;
    root_parameters[2].DescriptorTable.NumDescriptorRanges = 1;
    root_parameters[2].DescriptorTable.pDescriptorRanges = &srv_range;
    root_parameters[2].ShaderVisibility = D3D12_SHADER_VISIBILITY_PIXEL;

    std::array<D3D12_STATIC_SAMPLER_DESC, 3> samplers{};
    samplers[0].Filter = D3D12_FILTER_ANISOTROPIC;
    samplers[0].AddressU = D3D12_TEXTURE_ADDRESS_MODE_WRAP;
    samplers[0].AddressV = D3D12_TEXTURE_ADDRESS_MODE_WRAP;
    samplers[0].AddressW = D3D12_TEXTURE_ADDRESS_MODE_WRAP;
    samplers[0].MaxAnisotropy = 8;
    samplers[0].ComparisonFunc = D3D12_COMPARISON_FUNC_ALWAYS;
    samplers[0].MinLOD = 0.0f;
    samplers[0].MaxLOD = FLT_MAX;
    samplers[0].ShaderRegister = 0;
    samplers[0].ShaderVisibility = D3D12_SHADER_VISIBILITY_PIXEL;

    samplers[1].Filter = D3D12_FILTER_COMPARISON_MIN_MAG_LINEAR_MIP_POINT;
    samplers[1].AddressU = D3D12_TEXTURE_ADDRESS_MODE_BORDER;
    samplers[1].AddressV = D3D12_TEXTURE_ADDRESS_MODE_BORDER;
    samplers[1].AddressW = D3D12_TEXTURE_ADDRESS_MODE_BORDER;
    samplers[1].ComparisonFunc = D3D12_COMPARISON_FUNC_LESS_EQUAL;
    samplers[1].BorderColor = D3D12_STATIC_BORDER_COLOR_OPAQUE_WHITE;
    samplers[1].MinLOD = 0.0f;
    samplers[1].MaxLOD = FLT_MAX;
    samplers[1].ShaderRegister = 1;
    samplers[1].ShaderVisibility = D3D12_SHADER_VISIBILITY_PIXEL;

    samplers[2].Filter = D3D12_FILTER_MIN_MAG_MIP_LINEAR;
    samplers[2].AddressU = D3D12_TEXTURE_ADDRESS_MODE_CLAMP;
    samplers[2].AddressV = D3D12_TEXTURE_ADDRESS_MODE_CLAMP;
    samplers[2].AddressW = D3D12_TEXTURE_ADDRESS_MODE_CLAMP;
    samplers[2].ComparisonFunc = D3D12_COMPARISON_FUNC_ALWAYS;
    samplers[2].MinLOD = 0.0f;
    samplers[2].MaxLOD = FLT_MAX;
    samplers[2].ShaderRegister = 2;
    samplers[2].ShaderVisibility = D3D12_SHADER_VISIBILITY_PIXEL;

    D3D12_ROOT_SIGNATURE_DESC root_description{};
    root_description.NumParameters = static_cast<UINT>(root_parameters.size());
    root_description.pParameters = root_parameters.data();
    root_description.NumStaticSamplers = static_cast<UINT>(samplers.size());
    root_description.pStaticSamplers = samplers.data();
    root_description.Flags = D3D12_ROOT_SIGNATURE_FLAG_ALLOW_INPUT_ASSEMBLER_INPUT_LAYOUT
        | D3D12_ROOT_SIGNATURE_FLAG_DENY_HULL_SHADER_ROOT_ACCESS
        | D3D12_ROOT_SIGNATURE_FLAG_DENY_DOMAIN_SHADER_ROOT_ACCESS
        | D3D12_ROOT_SIGNATURE_FLAG_DENY_GEOMETRY_SHADER_ROOT_ACCESS;

    ComPtr<ID3DBlob> serialized_root_signature;
    ComPtr<ID3DBlob> root_error;
    const HRESULT serialization_result = D3D12SerializeRootSignature(
        &root_description, D3D_ROOT_SIGNATURE_VERSION_1,
        &serialized_root_signature, &root_error);
    if (FAILED(serialization_result))
    {
        const std::string error_text = root_error != nullptr
            ? std::string(static_cast<const char*>(root_error->GetBufferPointer()), root_error->GetBufferSize())
            : "unknown root-signature error";
        throw std::runtime_error("Phase 5 root signature serialization failed: " + error_text);
    }
    ThrowIfFailed(
        device_->CreateRootSignature(
            0, serialized_root_signature->GetBufferPointer(),
            serialized_root_signature->GetBufferSize(), IID_PPV_ARGS(&root_signature_)),
        "ID3D12Device::CreateRootSignature");
    NameObject(root_signature_.Get(), L"MARSTHEGAME Phase 5 Root Signature");

    const std::array<D3D12_INPUT_ELEMENT_DESC, 3> input_layout = {{
        {"POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0,
         D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
        {"NORMAL", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 12,
         D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
        {"COLOR", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 24,
         D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
    }};

    D3D12_GRAPHICS_PIPELINE_STATE_DESC shadow_description{};
    shadow_description.pRootSignature = root_signature_.Get();
    shadow_description.VS = {shadow_vs.data(), shadow_vs.size()};
    shadow_description.BlendState = OpaqueBlendDescription();
    shadow_description.SampleMask = (std::numeric_limits<UINT>::max)();
    shadow_description.RasterizerState = RasterizerDescription();
    shadow_description.RasterizerState.DepthBias = 2'400;
    shadow_description.RasterizerState.SlopeScaledDepthBias = 2.0f;
    shadow_description.DepthStencilState = DepthDescription(true, true);
    shadow_description.InputLayout = {input_layout.data(), static_cast<UINT>(input_layout.size())};
    shadow_description.PrimitiveTopologyType = D3D12_PRIMITIVE_TOPOLOGY_TYPE_TRIANGLE;
    shadow_description.NumRenderTargets = 0;
    shadow_description.DSVFormat = DXGI_FORMAT_D32_FLOAT;
    shadow_description.SampleDesc.Count = 1;
    ThrowIfFailed(device_->CreateGraphicsPipelineState(&shadow_description, IID_PPV_ARGS(&shadow_pipeline_)),
                  "ID3D12Device::CreateGraphicsPipelineState(shadow)");

    D3D12_GRAPHICS_PIPELINE_STATE_DESC scene_description = shadow_description;
    scene_description.VS = {scene_vs.data(), scene_vs.size()};
    scene_description.PS = {scene_ps.data(), scene_ps.size()};
    scene_description.RasterizerState = RasterizerDescription();
    scene_description.NumRenderTargets = 1;
    scene_description.RTVFormats[0] = DXGI_FORMAT_R16G16B16A16_FLOAT;
    ThrowIfFailed(device_->CreateGraphicsPipelineState(&scene_description, IID_PPV_ARGS(&scene_pipeline_)),
                  "ID3D12Device::CreateGraphicsPipelineState(scene)");

    D3D12_GRAPHICS_PIPELINE_STATE_DESC particle_description{};
    particle_description.pRootSignature = root_signature_.Get();
    particle_description.VS = {particle_vs.data(), particle_vs.size()};
    particle_description.PS = {particle_ps.data(), particle_ps.size()};
    particle_description.BlendState = OpaqueBlendDescription();
    particle_description.BlendState.RenderTarget[0].BlendEnable = TRUE;
    particle_description.BlendState.RenderTarget[0].SrcBlend = D3D12_BLEND_ONE;
    particle_description.BlendState.RenderTarget[0].DestBlend = D3D12_BLEND_ONE;
    particle_description.BlendState.RenderTarget[0].SrcBlendAlpha = D3D12_BLEND_ONE;
    particle_description.BlendState.RenderTarget[0].DestBlendAlpha = D3D12_BLEND_ONE;
    particle_description.SampleMask = (std::numeric_limits<UINT>::max)();
    particle_description.RasterizerState = RasterizerDescription();
    particle_description.DepthStencilState = DepthDescription(true, false);
    particle_description.PrimitiveTopologyType = D3D12_PRIMITIVE_TOPOLOGY_TYPE_TRIANGLE;
    particle_description.NumRenderTargets = 1;
    particle_description.RTVFormats[0] = DXGI_FORMAT_R16G16B16A16_FLOAT;
    particle_description.DSVFormat = DXGI_FORMAT_D32_FLOAT;
    particle_description.SampleDesc.Count = 1;
    ThrowIfFailed(device_->CreateGraphicsPipelineState(&particle_description, IID_PPV_ARGS(&particle_pipeline_)),
                  "ID3D12Device::CreateGraphicsPipelineState(particles)");

    D3D12_GRAPHICS_PIPELINE_STATE_DESC fullscreen_description{};
    fullscreen_description.pRootSignature = root_signature_.Get();
    fullscreen_description.VS = {fullscreen_vs.data(), fullscreen_vs.size()};
    fullscreen_description.BlendState = OpaqueBlendDescription();
    fullscreen_description.SampleMask = (std::numeric_limits<UINT>::max)();
    fullscreen_description.RasterizerState = RasterizerDescription();
    fullscreen_description.DepthStencilState = DepthDescription(false, false);
    fullscreen_description.PrimitiveTopologyType = D3D12_PRIMITIVE_TOPOLOGY_TYPE_TRIANGLE;
    fullscreen_description.NumRenderTargets = 1;
    fullscreen_description.SampleDesc.Count = 1;

    D3D12_GRAPHICS_PIPELINE_STATE_DESC temporal_description = fullscreen_description;
    temporal_description.PS = {temporal_ps.data(), temporal_ps.size()};
    temporal_description.RTVFormats[0] = DXGI_FORMAT_R16G16B16A16_FLOAT;
    ThrowIfFailed(device_->CreateGraphicsPipelineState(&temporal_description, IID_PPV_ARGS(&temporal_pipeline_)),
                  "ID3D12Device::CreateGraphicsPipelineState(temporal)");

    D3D12_GRAPHICS_PIPELINE_STATE_DESC final_description = fullscreen_description;
    final_description.PS = {final_ps.data(), final_ps.size()};
    final_description.RTVFormats[0] = DXGI_FORMAT_R8G8B8A8_UNORM;
    ThrowIfFailed(device_->CreateGraphicsPipelineState(&final_description, IID_PPV_ARGS(&final_pipeline_)),
                  "ID3D12Device::CreateGraphicsPipelineState(final)");

    NameObject(shadow_pipeline_.Get(), L"MARSTHEGAME Shadow Pipeline");
    NameObject(scene_pipeline_.Get(), L"MARSTHEGAME HDR PBR Pipeline");
    NameObject(particle_pipeline_.Get(), L"MARSTHEGAME Procedural Dust Pipeline");
    NameObject(temporal_pipeline_.Get(), L"MARSTHEGAME Temporal Resolve Pipeline");
    NameObject(final_pipeline_.Get(), L"MARSTHEGAME Tone Mapping Pipeline");
}

void D3D12Renderer::CreateStaticResources()
{
    const ProceduralMeshCatalog mesh_catalog = GenerateProceduralMeshCatalog();
    const GeneratedMaterialCatalog material_catalog = GenerateMaterialCatalog();
    if (!ValidateMaterialCatalog(material_catalog))
    {
        throw std::runtime_error("Generated material catalog failed validation");
    }
    static_assert(kProceduralMeshCount == kGeneratedMaterialCount);
    static_assert(kGeneratedMaterialCount == static_cast<std::size_t>(MeshKind::Count));

    std::vector<MeshVertex> vertices;
    std::vector<std::uint32_t> indices;
    for (std::size_t mesh_index = 0; mesh_index < mesh_catalog.meshes.size(); ++mesh_index)
    {
        const MeshData& mesh = mesh_catalog.meshes[mesh_index];
        if (!ValidateMesh(mesh))
        {
            throw std::runtime_error("Generated mesh atlas contains invalid topology");
        }
        if (vertices.size() > static_cast<std::size_t>((std::numeric_limits<std::int32_t>::max)())
            || indices.size() > static_cast<std::size_t>((std::numeric_limits<std::uint32_t>::max)())
            || mesh.indices.size() > static_cast<std::size_t>((std::numeric_limits<std::uint32_t>::max)()))
        {
            throw std::runtime_error("Generated mesh atlas exceeds renderer index limits");
        }
        mesh_ranges_[mesh_index] = {
            .index_count = static_cast<std::uint32_t>(mesh.indices.size()),
            .start_index = static_cast<std::uint32_t>(indices.size()),
            .base_vertex = static_cast<std::int32_t>(vertices.size()),
        };
        vertices.insert(vertices.end(), mesh.vertices.begin(), mesh.vertices.end());
        indices.insert(indices.end(), mesh.indices.begin(), mesh.indices.end());
    }

    upload_context_.Initialize(*device_.Get(), *command_queue_.Get());
    upload_context_.Begin();
    vertex_buffer_ = upload_context_.UploadBuffer(
        std::as_bytes(std::span<const MeshVertex>(vertices)),
