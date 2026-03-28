# Tectonic Grid Solver

Welcome to the repository of the Tectonic Grid Solver. This complete application allows users to import, generate, and solve Tectonic puzzles.

This project is composed of several technical domains:
- GUI Development & Core Compilation
- Image Processing
- Optical Character Recognition (OCR) / Digit Recognition
- SAT & HADOC Solvers


## Main Features

### Interactive User Interface
- **Start Menu:** Choose to import a custom grid or generate a random puzzle at startup.
- **Input Controls:** Fully interactive with keyboard and mouse to select and fill cells.
- **Draft Mode:** Add small corner notes to test hypotheses before committing to a number.
- **Responsive Design:** Resizable window with a UI that dynamically adapts to screen and grid dimensions.

### Level Generator
- Random creation of grids with variable sizes (AxB, where A and B are between 5 and 9) and randomized zones.
- Utilizes a SAT solver to guarantee that every generated grid has a valid, unique solution.
- *Note: Grid generation is computationally intensive and may take up to 3 minutes.*

### Custom Grid Import
- Take a picture of a physical Tectonic puzzle and import the image.
- The application processes the image, recognizes the grid layout and digits, and reconstructs the playable puzzle in the interface.
- Concurrently, the data is sent to MiniSAT to compute the final solution.

### Assistance Tools
- **Verify:** Real-time comparison of your inputs against the solution (green/red indicators).
- **Hint:** A logical solver provides the next best move based on your current progress.
- **Solve:** Instantly completes the grid using MiniSAT.


## Getting Started

To launch the application, simply run the main script:
- 'interface_tectonic.py'
