            }
            if (saved_checkpoint && !game.CheckpointReached())
            {
                saved_checkpoint = false;
            }
            if (renderer.PresentedFrameCount() % 120U == 0U)
            {
                LogFrameStatistics(renderer.Statistics());
            }
        }
        renderer.Shutdown();
        return 0;
    }
    catch (const std::exception& error)
    {
        const std::wstring message = ToWide(error.what());
        OutputDebugStringW(message.c_str());
        if (!self_test && !warp_smoke_test)
        {
            MessageBoxW(nullptr, message.c_str(), L"MARSTHEGAME native failure", MB_OK | MB_ICONERROR);
        }
        return 1;
    }
}
