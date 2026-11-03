use tauri::Manager;
use tauri::WindowEvent;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use std::sync::Mutex;

struct BackendChild(Mutex<Option<CommandChild>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let (mut rx, child) = app
                .shell()
                .sidecar("sovriva-backend")
                .expect("sidecar configured")
                .spawn()
                .expect("SOVRIVA backend sidecar should start");
            app.manage(BackendChild(Mutex::new(Some(child))));
            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    if let CommandEvent::Error(error) = event {
                        eprintln!("SOVRIVA backend: {error}");
                    }
                }
            });
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { .. } = event {
                if let Some(state) = window.app_handle().try_state::<BackendChild>() {
                    if let Ok(mut child) = state.0.lock() {
                        if let Some(mut process) = child.take() {
                            let _ = process.kill();
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running SOVRIVA desktop");
}
