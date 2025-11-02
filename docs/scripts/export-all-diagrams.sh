#!/bin/bash

# =============================================
# CodeGuard AI - Diagram Export (WORKING)
# =============================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  CodeGuard AI - Diagram Export            ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}\n"

# Check Java
if ! command -v java &> /dev/null; then
    echo -e "${RED}[ERROR] Java not found${NC}"
    exit 1
fi

# Check Graphviz
if ! command -v dot &> /dev/null; then
    echo -e "${RED}[ERROR] Graphviz not found. Install: sudo apt install graphviz${NC}"
    exit 1
fi

echo -e "${GREEN}[✓] Dependencies OK${NC}\n"

# PlantUML JAR
PLANTUML="$HOME/.local/share/plantuml/plantuml.jar"

# Download PlantUML if needed
if [ ! -f "$PLANTUML" ]; then
    echo -e "${YELLOW}[*] Downloading PlantUML...${NC}"
    mkdir -p "$HOME/.local/share/plantuml"
    wget -q https://github.com/plantuml/plantuml/releases/download/v1.2024.7/plantuml-1.2024.7.jar -O "$PLANTUML"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[✓] PlantUML downloaded${NC}\n"
    else
        echo -e "${RED}[ERROR] Failed to download PlantUML${NC}"
        exit 1
    fi
fi

# Create export directories
mkdir -p exports/{png,svg,pdf}

# Find all .puml files into an array
mapfile -t FILES < <(find . -name "*.puml" -type f | sort)

TOTAL=${#FILES[@]}

echo -e "${YELLOW}[*] Found $TOTAL PlantUML files${NC}\n"

if [ "$TOTAL" -eq 0 ]; then
    echo -e "${RED}[ERROR] No .puml files found!${NC}"
    exit 1
fi

# Export each file
COUNT=0
for file in "${FILES[@]}"; do
    ((COUNT++))
    
    # Get category (folder name)
    category=$(basename "$(dirname "$file")")
    filename=$(basename "$file" .puml)
    
    # Create subdirectories
    mkdir -p "exports/png/$category"
    mkdir -p "exports/svg/$category"
    mkdir -p "exports/pdf/$category"
    
    echo -e "${YELLOW}[$COUNT/$TOTAL]${NC} ${filename} ${GREEN}(${category})${NC}"
    
    # Export to PNG
    java -jar "$PLANTUML" -tpng -o "$(pwd)/exports/png/$category" "$file" > /dev/null 2>&1
    
    # Export to SVG
    java -jar "$PLANTUML" -tsvg -o "$(pwd)/exports/svg/$category" "$file" > /dev/null 2>&1
    
    # Export to PDF
    java -jar "$PLANTUML" -tpdf -o "$(pwd)/exports/pdf/$category" "$file" > /dev/null 2>&1
    
    echo -e "  ${GREEN}✓${NC} PNG | SVG | PDF"
done

# Summary
echo -e "\n${GREEN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Export Complete!                         ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}\n"

PNG_COUNT=$(find exports/png -name "*.png" -type f 2>/dev/null | wc -l)
SVG_COUNT=$(find exports/svg -name "*.svg" -type f 2>/dev/null | wc -l)
PDF_COUNT=$(find exports/pdf -name "*.pdf" -type f 2>/dev/null | wc -l)

echo -e "  PNG: ${YELLOW}$PNG_COUNT${NC}  |  SVG: ${YELLOW}$SVG_COUNT${NC}  |  PDF: ${YELLOW}$PDF_COUNT${NC}"
echo -e "\n  📁 Location: ${YELLOW}$(pwd)/exports${NC}\n"

# Open exports folder (optional)
echo -e "${YELLOW}[?] View exports folder?${NC}"
echo -e "Run: ${GREEN}cd exports && ls -lh${NC}\n"
