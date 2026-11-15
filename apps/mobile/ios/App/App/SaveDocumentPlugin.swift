import Foundation
import UIKit
import Capacitor

/// Exports through the system document picker. No HTTP, app server or broad file access.
@objc(SaveDocumentPlugin)
public class SaveDocumentPlugin: CAPPlugin, CAPBridgedPlugin, UIDocumentPickerDelegate {
    public let identifier = "SaveDocumentPlugin"
    public let jsName = "SaveDocument"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "save", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "clear", returnType: CAPPluginReturnPromise)
    ]
    private var pending: CAPPluginCall?
    private var temporaryFolder: URL?
    private var cache: URL {
        FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("runaway-exports", isDirectory: true)
    }

    @objc func save(_ call: CAPPluginCall) {
        guard let name = call.getString("name"),
              name.range(of: "^[A-Za-z0-9_.-]{1,120}$", options: .regularExpression) != nil,
              let encoded = call.getString("data"), encoded.count <= 2_800_000,
              let data = Data(base64Encoded: encoded),
              let mime = call.getString("mime"),
              ["application/json", "application/zip", "text/plain"].contains(mime)
        else { call.reject("无效的导出文件。"); return }
        DispatchQueue.main.async {
            guard self.pending == nil, let controller = self.bridge?.viewController else {
                call.reject("请先完成当前文件保存。"); return
            }
            self.pending = call
            let folder = self.cache.appendingPathComponent(UUID().uuidString, isDirectory: true)
            self.temporaryFolder = folder
            do {
                try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
                let file = folder.appendingPathComponent(name)
                try data.write(to: file, options: .atomic)
                let picker = UIDocumentPickerViewController(forExporting: [file], asCopy: true)
                picker.delegate = self
                picker.directoryURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
                picker.modalPresentationStyle = .formSheet
                controller.present(picker, animated: true)
            } catch {
                self.finish(error: "文件未能准备好，请重新导出。")
            }
        }
    }

    public func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
        guard !urls.isEmpty else { finish(error: "已取消保存。"); return }
        pending?.resolve(["status": "saved"])
        cleanup()
    }
    public func documentPickerWasCancelled(_ controller: UIDocumentPickerViewController) {
        finish(error: "已取消保存。")
    }
    private func finish(error: String) { pending?.reject(error); cleanup() }
    private func cleanup() {
        if let folder = temporaryFolder { try? FileManager.default.removeItem(at: folder) }
        pending = nil
        temporaryFolder = nil
    }
    @objc func clear(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            guard self.pending == nil else { call.reject("请先完成当前文件保存。"); return }
            do {
                if FileManager.default.fileExists(atPath: self.cache.path) {
                    try FileManager.default.removeItem(at: self.cache)
                }
                call.resolve()
            } catch { call.reject("上次导出留下的临时文件未能清理。") }
        }
    }
}
