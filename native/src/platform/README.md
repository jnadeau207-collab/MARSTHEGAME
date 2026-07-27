# Native Platform Layer

The Win32 layer owns the game window, message pump, resize notifications, and shutdown behavior. Gameplay input is currently polled through the Windows virtual-key state and will move behind the Phase 4 native input abstraction.
