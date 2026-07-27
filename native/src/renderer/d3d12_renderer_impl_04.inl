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
    const GeneratedEnvironmentCube environment = GenerateAresReachEnvironmentCube();
    if (!ValidateMaterialCatalog(material_catalog))
    {
        throw std::runtime_error("Generated material catalog failed validation");
    }
    if (!ValidateEnvironmentCube(environment))
    {
        throw std::runtime_error("Generated environment IBL cube failed validation");
    }
    static_assert(kProceduralMeshCount == static_cast<std::size_t>(MeshKind::Count));
    static_assert(kGeneratedMaterialCount >= kProceduralMeshCount);

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
            throw std::runtime_error("Generated mesh atlas exceeds D3D12 index limits");
        }
        MeshRange& range = mesh_ranges_[mesh_index];
        range.index_count = CheckedSizeToUint(mesh.indices.size(), "generated mesh index count");
        range.start_index = CheckedSizeToUint(indices.size(), "generated mesh start index");
        range.base_vertex = static_cast<std::int32_t>(vertices.size());
        vertices.insert(vertices.end(), mesh.vertices.begin(), mesh.vertices.end());
        indices.insert(indices.end(), mesh.indices.begin(), mesh.indices.end());
    }
    if (vertices.empty() || indices.empty())
    {
        throw std::runtime_error("Generated mesh atlas is empty");
    }

    upload_context_.Initialize(*device_.Get());
    vertex_buffer_ = upload_context_.UploadBuffer(
        std::as_bytes(std::span<const MeshVertex>(vertices)),
        D3D12_RESOURCE_STATE_VERTEX_AND_CONSTANT_BUFFER,
        L"MARSTHEGAME Default-Heap Procedural Vertices");
    index_buffer_ = upload_context_.UploadBuffer(
        std::as_bytes(std::span<const std::uint32_t>(indices)),
        D3D12_RESOURCE_STATE_INDEX_BUFFER,
        L"MARSTHEGAME Default-Heap Procedural Indices");
    base_color_texture_ = upload_context_.UploadTexture2DArrayRgba8(
        std::span<const std::uint8_t>(material_catalog.base_color.rgba8),
        material_catalog.base_color.width,
        material_catalog.base_color.height,
        material_catalog.base_color.layers,
        D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE,
        L"MARSTHEGAME Generated Base Color Array");
    normal_texture_ = upload_context_.UploadTexture2DArrayRgba8(
        std::span<const std::uint8_t>(material_catalog.normal.rgba8),
        material_catalog.normal.width,
        material_catalog.normal.height,
        material_catalog.normal.layers,
        D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE,
        L"MARSTHEGAME Generated Normal Array");
    surface_texture_ = upload_context_.UploadTexture2DArrayRgba8(
        std::span<const std::uint8_t>(material_catalog.surface.rgba8),
        material_catalog.surface.width,
        material_catalog.surface.height,
        material_catalog.surface.layers,
        D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE,
        L"MARSTHEGAME Generated Roughness Metallic Mask Array");
    environment_texture_ = upload_context_.UploadTexture2DArrayRgba8(
        std::span<const std::uint8_t>(environment.rgba8),
        environment.face_size,
        environment.face_size,
        6U,
        D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE,
        L"MARSTHEGAME Generated Martian Environment Cube");
