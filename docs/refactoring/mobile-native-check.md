# Native iOS build check — 18 October 2026

The isolated Release build succeeded with Xcode 26.6 (17F113), iOS Simulator SDK 26.5, arm64, code signing disabled. The final build took 295 seconds with four jobs and `ONLY_ACTIVE_ARCH=YES`. It uses the final mobile/packages source snapshot recorded in `artifacts/mobile-native/source-manifest.json`.

The deliverable is `artifacts/mobile-native/NumerOM-ios-simulator-arm64.zip` (19,738,391 bytes). It contains `NumerOM.app`, including the Mach-O executable and bundled JavaScript. ZIP integrity passed; Pods and DerivedData are excluded. This is a Simulator application, not an IPA or App Store release.

Verified in the compiled application:

- Bundle identifier `com.numerom.app`, version `0.1.0`; arm64 executable and `main.jsbundle` present.
- Production HTTPS API origin is stored in `EXConstants.bundle/app.config` and read through `Constants.expoConfig.extra.apiUrl`: `https://witnesses-vpn-dare-heavily.trycloudflare.com`. This temporary tunnel must remain available for server operations.
- The native AppIcon is 1024×1024 RGB and matches the source logo rendering pixel for pixel.
- Face ID usage description is present. No microphone permission or background audio mode is requested.
- Both `NSAllowsArbitraryLoads` and `NSAllowsLocalNetworking` are explicitly false for production; the development branch is unchanged. TypeScript checking passed after this change.
- Native registration includes audio, SecureStore, document picker, filesystem, PDF printing, and sharing modules. Compilation does not establish their physical-device behavior.

The clean `NumerOM-QA-20261018` iPhone 17 Pro simulator (iOS 26.5, UDID `8B3394E4-BD2B-4107-8F56-53C6561A6B11`) completed boot, and `simctl install` returned exit 0. The subsequent `cua.getApp("Simulator")` call returned no UI state and was interrupted after 332.2 seconds. No approval rejection was reported. A login screen was not observed, so native UI startup remains **not verified**. The agent-owned simulator was shut down after installation was recorded and was not deleted. No account was entered and no license or agreement was accepted.

Physical Face ID/Touch ID, device installation, distribution signing, App Store delivery, and Android native compilation are outside the evidence provided by this build. Full hashes, native permissions, module registration, build logs, and the archive checksum are recorded in `artifacts/mobile-native/verification.json` and adjacent files.
