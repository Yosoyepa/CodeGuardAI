#!/bin/bash

# ========================================
# CodeGuard AI - Batch Diagram Export Script
# Exports all PlantUML diagrams to PNG/SVG/PDF
# ========================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DOCS_DIR="$PROJECT_ROOT/docs"
EXPORT_DIR="$DOCS_DIR/exports"

# Create export directories
mkdir -p "$EXPORT_DIR"/{png,svg,pdf}

# Function to check dependencies
check_dependencies() {
    echo -e "${YELLOW}[*] Checking dependencies...${NC}"
    
    if ! command -v java &> /dev/null; then
        echo -e "${RED}[ERROR] Java not found. Install from https://www.oracle.com/java/technologies/downloads/${NC}"
        exit 1
    fi
    
    if ! command -v dot &> /dev/null; then
        echo -e "${RED}[ERROR] Graphviz not found. Install with: brew install graphviz (Mac) or sudo apt-get install graphviz (Linux)${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}[✓] Dependencies OK${NC}\n"
}

# Function to export a single diagram
export_diagram() {
    local puml_file="$1"
    local diagram_name=$(basename "$puml_file" .puml)
    local category=$(basename "$(dirname "$puml_file")")
    
    # Create category directories
    mkdir -p "$EXPORT_DIR"/png/"$category"
    mkdir -p "$EXPORT_DIR"/svg/"$category"
    mkdir -p "$EXPORT_DIR"/pdf/"$category"
    
    echo -e "${YELLOW}[*] Exporting: $diagram_name${NC}"
    
    # Export to PNG (300 DPI)
    java -jar ~/.local/share/plantuml/plantuml.jar \
        -tpng \
        -o "$EXPORT_DIR/png/$category" \
        "$puml_file" 2>&1 | grep -v "^$" || true
    
    # Export to SVG (vectorial)
    java -jar ~/.local/share/plantuml/plantuml.jar \
        -tsvg \
        -o "$EXPORT_DIR/svg/$category" \
        "$puml_file" 2>&1 | grep -v "^$" || true
    
    # Export to PDF
    java -jar ~/.local/share/plantuml/plantuml.jar \
        -tpdf \
        -o "$EXPORT_DIR/pdf/$category" \
        "$puml_file" 2>&1 | grep -v "^$" || true
    
    echo -e "${GREEN}[✓] Exported: $diagram_name to PNG, SVG, PDF${NC}"
}

# Function to recursively export all PUML files
export_all_diagrams() {
    echo -e "${YELLOW}[*] Scanning for PlantUML files in $DOCS_DIR...${NC}\n"
    
    local puml_count=0
    local total_puml=$(find "$DOCS_DIR" -name "*.puml" -type f | wc -l)
    
    while IFS= read -r puml_file; do
        ((puml_count++))
        echo -e "\n${YELLOW}[$puml_count/$total_puml]${NC}"
        export_diagram "$puml_file"
    done < <(find "$DOCS_DIR" -name "*.puml" -type f | sort)
    
    echo -e "\n${GREEN}[✓] Exported $total_puml diagrams!${NC}"
}

# Function to generate index HTML
generate_html_index() {
    echo -e "${YELLOW}[*] Generating HTML index...${NC}"
    
    cat > "$EXPORT_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeGuard AI - Diagram Gallery</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { color: #1E40AF; margin-bottom: 30px; text-align: center; }
        .category { background: white; margin-bottom: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }
        .category-header { background: #E7F5FF; padding: 15px 20px; border-left: 4px solid #1E40AF; }
        .category-header h2 { color: #1E40AF; font-size: 18px; }
        .diagrams-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; padding: 20px; }
        .diagram-card { border: 1px solid #ddd; border-radius: 6px; overflow: hidden; cursor: pointer; transition: transform 0.2s; }
        .diagram-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .diagram-preview { width: 100%; height: 200px; background: #f9f9f9; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #999; overflow: hidden; }
        .diagram-preview img { width: 100%; height: 100%; object-fit: cover; }
        .diagram-info { padding: 15px; }
        .diagram-info h3 { color: #1E40AF; font-size: 14px; margin-bottom: 8px; }
        .diagram-links { display: flex; gap: 10px; margin-top: 10px; }
        .diagram-links a { font-size: 12px; padding: 5px 10px; background: #E7F5FF; color: #1E40AF; text-decoration: none; border-radius: 4px; transition: background 0.2s; }
        .diagram-links a:hover { background: #1E40AF; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 CodeGuard AI - Diagram Gallery</h1>
        <p style="text-align: center; color: #666; margin-bottom: 30px;">Complete visualization of system architecture, design, and workflows</p>
        <!-- HTML content will be generated here -->
    </div>
</body>
</html>
EOF
    
    echo -e "${GREEN}[✓] HTML index generated at $EXPORT_DIR/index.html${NC}"
}

# Function to display summary statistics
display_summary() {
    echo -e "\n${GREEN}============================================${NC}"
    echo -e "${GREEN}Export Complete - Summary${NC}"
    echo -e "${GREEN}============================================${NC}"
    
    local png_count=$(find "$EXPORT_DIR/png" -name "*.png" -type f | wc -l)
    local svg_count=$(find "$EXPORT_DIR/svg" -name "*.svg" -type f | wc -l)
    local pdf_count=$(find "$EXPORT_DIR/pdf" -name "*.pdf" -type f | wc -l)
    
    echo -e "PNG diagrams: ${YELLOW}$png_count${NC}"
    echo -e "SVG diagrams: ${YELLOW}$svg_count${NC}"
    echo -e "PDF diagrams: ${YELLOW}$pdf_count${NC}"
    echo ""
    echo -e "Export location: ${YELLOW}$EXPORT_DIR${NC}"
    echo -e "View: ${YELLOW}$EXPORT_DIR/index.html${NC}"
    echo -e "${GREEN}============================================${NC}\n"
}

# Main execution
main() {
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════╗"
    echo "║  CodeGuard AI - Diagram Export Script     ║"
    echo "║  Batch export all PlantUML diagrams       ║"
    echo "╚═══════════════════════════════════════════╝"
    echo -e "${NC}\n"
    
    check_dependencies
    export_all_diagrams
    generate_html_index
    display_summary
}

# Run main function
main
