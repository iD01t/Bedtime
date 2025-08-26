# Bedtime Story Maker - v3.0.0 Premium

**Created by Guillaume Lessard, Senior Product Engineer for iD01t Productions**

Welcome to the Bedtime Story Maker, a premium, offline-first desktop application designed to help you create, manage, and share unique and personalized bedtime stories for children.

![Screenshot Placeholder](https://via.placeholder.com/800x500.png?text=App+Screenshot+Here)
*(Screenshot placeholder: The main application interface)*

## Features

This application is built with a focus on a high-quality user experience, robust offline capabilities, and powerful content generation.

*   **Modern, Responsive UI**: A clean, "React-style" interface with a pastel theme, cards, and clear typography that feels at home on a modern desktop.
*   **Offline-First Engine**: The core story generation works entirely offline. It uses a built-in set of templates, but can be overridden by an external `content_creators.json` file for easy customization.
*   **Bilingual Support**: Full UI and theme support for both English and French, which can be switched dynamically.
*   **Unique Story Generation**:
    *   The generator never produces the same story twice, even with identical inputs, thanks to a random salt.
    *   A modular content engine picks from various templates for intros, middles, and climaxes to ensure variety.
    *   Customize stories with parameters like topic, character name, age, tone, and theme.
*   **Premium Library**:
    *   Save your favorite generated stories to a local JSON-based library.
    *   Load, delete, and manage your stories.
    *   Mark stories as "Favorites" with a star for easy access.
    *   Search your library by title or content.
    *   Sort stories by creation date or title.
    *   Undo a mistaken deletion.
*   **Versatile Export Options**:
    *   Export any story with a single click to multiple formats:
        *   **TXT**: Plain text for easy sharing.
        *   **HTML**: A responsive, self-contained HTML file with clean styling.
        *   **PDF**: A print-friendly PDF document (requires `reportlab`).
    *   Uses a customizable filename pattern for organized exports.
*   **Comprehensive Settings**:
    *   Persists all user choices in a local `settings.json` file.
    *   Configure UI language, export defaults, and more.
    *   Optional, privacy-first integration for a Gemini API key (stored locally with simple encryption).
*   **Accessibility & UX**:
    *   Full keyboard navigation support, including shortcuts.
    *   Tooltips for all interactive controls.
    *   Friendly empty states, confirmation dialogs, and a first-run tour.

## Setup & Running the Application

This application is designed to be run from a single Python file with minimal dependencies.

**Requirements:**
*   Python 3.9+
*   Tkinter (usually included with Python)

**Optional Dependencies:**
For full functionality, you can install the following libraries:
*   **Pillow**: For displaying icons (like the 'favorite' star) more reliably.
    ```bash
    pip install Pillow
    ```
*   **reportlab**: To enable PDF export.
    ```bash
    pip install reportlab
    ```

**Running the App:**
Simply run the `main.py` file with Python:
```bash
python main.py
```

## Packaging for Distribution

You can package the application into a single executable file using `PyInstaller`.

1.  Install PyInstaller:
    ```bash
    pip install pyinstaller
    ```
2.  Place an icon file named `icon.ico` in the same directory as `main.py`.
3.  Run the following command from your terminal in the project directory:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --icon=icon.ico main.py
    ```
4.  The final executable will be located in the `dist` folder.

## Keyboard Shortcuts

*   **Ctrl+N**: Create a new, blank story form.
*   **Ctrl+S**: Save the currently displayed story to the library.
*   **Ctrl+E**: Opens the Export menu (note: this is not explicitly bound, but the menu shows the accelerator).
