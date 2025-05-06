# Spotify Downloader UI Architecture

## UI Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│                              SPOTIFY DOWNLOADER UI                            │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                                UI LAYER                                       │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌────────────────────────┐    │
│  │                 │  │                     │  │                        │    │
│  │  Main Window    │  │  Playlist Input     │  │  Results Display       │    │
│  │  (QMainWindow)  │  │  (QWidget)          │  │  (QWidget)             │    │
│  │                 │  │                     │  │                        │    │
│  └─────────────────┘  └─────────────────────┘  └────────────────────────┘    │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌────────────────────────┐    │
│  │                 │  │                     │  │                        │    │
│  │  Progress View  │  │  Settings Dialog    │  │  Hidden Gems View      │    │
│  │  (QWidget)      │  │  (QDialog)          │  │  (QWidget)             │    │
│  │                 │  │                     │  │                        │    │
│  └─────────────────┘  └─────────────────────┘  └────────────────────────┘    │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                             CONTROLLER LAYER                                  │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌────────────────────────┐    │
│  │                 │  │                     │  │                        │    │
│  │  App Controller │  │  Playlist           │  │  Settings              │    │
│  │                 │  │  Controller         │  │  Controller            │    │
│  │                 │  │                     │  │                        │    │
│  └─────────────────┘  └─────────────────────┘  └────────────────────────┘    │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                             SERVICE LAYER                                     │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌────────────────────────┐    │
│  │                 │  │                     │  │                        │    │
│  │  Playlist       │  │  Spotify            │  │  Config                │    │
│  │  Service        │  │  Service            │  │  Service               │    │
│  │                 │  │                     │  │                        │    │
│  └─────────────────┘  └─────────────────────┘  └────────────────────────┘    │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────────┐                                │
│  │                 │  │                     │                                │
│  │  Analysis       │  │  Error Handling     │                                │
│  │  Service        │  │  Service            │                                │
│  │                 │  │                     │                                │
│  └─────────────────┘  └─────────────────────┘                                │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                             MODEL LAYER                                       │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌────────────────────────┐    │
│  │                 │  │                     │  │                        │    │
│  │  Playlist       │  │  Track              │  │  Settings              │    │
│  │  Model          │  │  Model              │  │  Model                 │    │
│  │                 │  │                     │  │                        │    │
│  └─────────────────┘  └─────────────────────┘  └────────────────────────┘    │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                            BACKEND (EXISTING)                                 │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                         │  │
│  │                    spotify_playlist_extractor.py                        │  │
│  │                                                                         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Key Principles

1. **Separation of Concerns**: UI logic is cleanly separated from business logic
2. **Service Layer**: All backend interactions go through service layer abstractions
3. **MVC Pattern**: Model-View-Controller pattern for UI organization
4. **Thread Management**: Background processing for non-UI operations

## Data Flow

1. User interacts with UI components in the View layer
2. Controllers process user actions and interact with Services
3. Services communicate with backend functionality
4. Backend processes data and returns results
5. Services transform results to appropriate model objects
6. Controllers update Views with model data
7. Views display updated information to the user

## Error Handling Flow

1. Backend errors are captured by Service layer
2. Services translate technical errors to user-friendly messages
3. Controllers present errors through appropriate UI mechanisms
4. Global error handler provides consistent error handling

## Threading Model

1. UI operations run on main thread
2. Backend operations run on worker threads
3. Communication via Qt signals/slots mechanism
4. Thread-safe data passing between layers

## Configuration Management

1. Settings stored in user-specific location
2. Configuration service provides unified access
3. Settings persisted between application runs
4. Defaults provided for first-time users 