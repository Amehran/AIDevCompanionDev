# AI Dev Companion - Android Client

> **Native Android Application for AI-Powered Code Analysis**
> A modern, Jetpack Compose-based Android application that interfaces with the AI Dev Companion backend to provide real-time Kotlin code analysis and assistance.

## 📱 Features

- **Interactive Chat Interface**: Natural language conversation with the AI assistant.
- **Code Analysis Mode**: Specialized mode for analyzing Kotlin code snippets.
- **Syntax Highlighting**: Beautiful rendering of code blocks and Markdown responses.
- **Local History**: Saves your conversations locally using Room Database.
- **Smart Suggestions**: Quick actions based on AI analysis (e.g., "Fix Issues", "Explain").
- **Resilient Networking**: Robust error handling and connection health checks.

## 🛠️ Tech Stack

- **Language**: [Kotlin](https://kotlinlang.org/)
- **UI Framework**: [Jetpack Compose](https://developer.android.com/jetpack/compose) (Material 3)
- **Architecture**: MVVM + Clean Architecture (UI, Domain, Data layers)
- **Dependency Injection**: [Hilt](https://dagger.dev/hilt/)
- **Networking**: [Retrofit](https://square.github.io/retrofit/) + [OkHttp](https://square.github.io/okhttp/)
- **Local Storage**: [Room Database](https://developer.android.com/training/data-storage/room)
- **Concurrency**: [Coroutines](https://kotlinlang.org/docs/coroutines-overview.html) + [Flow](https://kotlinlang.org/docs/flow)
- **Testing**: JUnit 4, Mockk, Turbine

## 🏗️ Architecture

The application follows the **Clean Architecture** principles:

- **UI Layer**: Composable screens (`ChatScreen`, `IntroScreen`) and ViewModels (`ChatViewModel`).
- **Domain Layer**: Use Cases (`SendMessageUseCase`, `CheckHealthUseCase`) and Domain Models.
- **Data Layer**: Repositories (`ChatRepositoryImpl`), Data Sources (`ApiService`, `ConversationDao`), and Mappers.

```mermaid
graph TD
    UI[UI Layer\n(Compose + ViewModel)] --> Domain[Domain Layer\n(Use Cases + Models)]
    Domain --> Data[Data Layer\n(Repository + Sources)]
    Data --> Remote[Remote Data\n(Retrofit)]
    Data --> Local[Local Data\n(Room)]
```

## 🚀 Getting Started

### Prerequisites

- Android Studio Hedgehog | 2023.1.1 or newer
- JDK 17
- Android SDK 34

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Amehran/AIDevCompanionDev.git
   cd AIDevCompanionDev/android-client
   ```

2. **Open in Android Studio**:
   - Open Android Studio.
   - Select "Open" and navigate to the `android-client` directory.

3. **Configure Backend URL**:
   - The backend URL is configured in `app/build.gradle.kts` via `buildConfigField`.
   - Default: `https://mscwwpv7wxm4tlstkg2qjqydxa0xldaa.lambda-url.us-east-1.on.aws/`

4. **Build and Run**:
   - Connect an Android device or start an emulator.
   - Run the `app` configuration.

## 🧪 Testing

Run unit tests using Gradle:

```bash
./gradlew testDebugUnitTest
```

## 📂 Project Structure

```
com.aidevcompanion.app
├── data                # Data layer (API, DB, Repositories)
│   ├── local           # Room DB entities and DAO
│   ├── mapper          # Data mapping extensions
│   ├── model           # DTOs
│   ├── remote          # Retrofit service
│   └── repository      # Repository implementations
├── di                  # Hilt modules
├── domain              # Domain layer (Business Logic)
│   ├── model           # Domain models
│   ├── repository      # Repository interfaces
│   └── usecase         # Interactors
└── ui                  # UI layer (Presentation)
    ├── screens         # Composable screens
    ├── theme           # App theme and typography
    └── viewmodel       # ViewModels
```

## 🤝 Contributing

Contributions are welcome! Please follow the standard pull request process.

## 📄 License

This project is licensed under the MIT License.
