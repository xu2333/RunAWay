import XCTest

/// Real WebView + system document UI. Only the bundled fictional demo is used.
final class LocalFilesUITests: XCTestCase {
    private let app = XCUIApplication()

    override func setUpWithError() throws {
        continueAfterFailure = false
        app.launchArguments = ["-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
    }

    override func tearDownWithError() throws {
        if testRun?.hasSucceeded == false {
            print(app.debugDescription)
            let image = XCTAttachment(screenshot: app.screenshot())
            image.lifetime = .keepAlways
            add(image)
        }
        app.terminate()
    }

    private func reveal(_ element: XCUIElement, up: Bool = true) {
        for _ in 0..<10 {
            if element.exists && element.isHittable { return }
            if up { app.swipeUp() } else { app.swipeDown() }
        }
        XCTAssertTrue(element.exists && element.isHittable, "Element is not reachable: \(element)")
    }

    private func file(prefix: String) -> XCUIElement? {
        let matches = app.descendants(matching: .any)
            .matching(NSPredicate(format: "label BEGINSWITH %@", prefix)).allElementsBoundByIndex
        return matches.first { $0.isHittable && $0.elementType != .application && $0.elementType != .window }
    }

    func testNativeSaveCancelSaveAndReopenPrivateArchive() throws {
        let demo = app.buttons["试试虚构示例"]
        XCTAssertTrue(demo.waitForExistence(timeout: 20))
        demo.tap()
        XCTAssertTrue(app.staticTexts["纸上谈兵行动派"].waitForExistence(timeout: 20))

        let saveArchive = app.buttons["保存私有档案"]
        reveal(saveArchive)
        saveArchive.tap()
        let cancel = app.buttons["Cancel"].firstMatch
        XCTAssertTrue(cancel.waitForExistence(timeout: 15), "System document picker did not open")
        cancel.tap()

        // A cancelled save must release the pending call so the next save works.
        reveal(saveArchive)
        saveArchive.tap()
        let save = app.buttons["Save"].firstMatch
        XCTAssertTrue(save.waitForExistence(timeout: 15))
        XCTAssertTrue(save.isEnabled)
        save.tap()
        let dismissed = XCTNSPredicateExpectation(predicate: NSPredicate(format: "exists == false"), object: save)
        wait(for: [dismissed], timeout: 15)

        let clear = app.buttons["清空本次材料"]
        reveal(clear)
        clear.tap()
        XCTAssertTrue(app.alerts.firstMatch.waitForExistence(timeout: 5))
        app.alerts.firstMatch.buttons.allElementsBoundByIndex.last!.tap()

        let open = app.staticTexts["打开档案 / prompt"].firstMatch
        reveal(open, up: false)
        open.tap()
        for title in ["Choose File", "Choose Files"] {
            let option = app.buttons[title].firstMatch
            if option.waitForExistence(timeout: 2) { option.tap(); break }
        }
        if file(prefix: "runaway.private") == nil {
            let browse = app.buttons["Browse"].firstMatch
            if browse.exists && browse.isHittable { browse.tap() }
            let local = app.staticTexts["On My iPhone"].firstMatch
            if local.waitForExistence(timeout: 5) && local.isHittable { local.tap() }
            let folder = app.staticTexts["RunAWay"].firstMatch
            if folder.waitForExistence(timeout: 5) && folder.isHittable { folder.tap() }
        }
        guard let archive = file(prefix: "runaway.private") else {
            XCTFail("Saved archive is not visible in the native file picker")
            return
        }
        archive.tap()
        XCTAssertTrue(app.staticTexts["纸上谈兵行动派"].waitForExistence(timeout: 20))
        XCTAssertTrue(app.staticTexts["虚构示例 · 不是对你的判断"].waitForExistence(timeout: 10))
    }
}
