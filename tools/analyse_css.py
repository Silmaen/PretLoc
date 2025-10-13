"""
Script d'analyse des classes CSS utilisées dans les templates Django.
"""

import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple


# Liste de regex pour exclure certaines classes de l'analyse
EXCLUDED_CLASS_PATTERNS = [
    r"^fa-.*",  # Font Awesome
    r"^fas$",  # Font Awesome Solid
    r"^far$",  # Font Awesome Regular
    r"^fab$",  # Font Awesome Brands
    r"^flatpickr-.*",  # Flatpickr
    r"^select2-.*",  # Select2
    r"^vis-.*",  # Vis.js
    r"^message-.*",  # Django messages
    r"^status-.*",  # Timeline status classes
]


def is_excluded_class(class_name: str) -> bool:
    """Vérifie si une classe doit être exclue de l'analyse."""
    for pattern in EXCLUDED_CLASS_PATTERNS:
        if re.match(pattern, class_name):
            return True
    return False


def extract_css_classes(css_file: Path) -> Set[str]:
    """Extrait toutes les classes définies dans un fichier CSS."""
    classes = set()
    with open(css_file, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    pattern = r"\.([a-zA-Z_][a-zA-Z0-9_-]*)\b"

    for match in re.finditer(pattern, content):
        class_name = match.group(1)
        if not re.match(r"^\d", class_name) and not is_excluded_class(class_name):
            classes.add(class_name)

    return classes


def extract_all_css_classes(css_dir: Path) -> Tuple[Set[str], Dict[str, Set[str]]]:
    """Extrait toutes les classes de tous les fichiers CSS du répertoire."""
    all_classes = set()
    classes_by_file = {}

    for css_file in css_dir.glob("*.css"):
        file_classes = extract_css_classes(css_file)
        classes_by_file[css_file.name] = file_classes
        all_classes.update(file_classes)

    return all_classes, classes_by_file


def extract_template_classes(template_file: Path) -> List[str]:
    """Extrait toutes les classes utilisées dans un template HTML."""
    classes = []
    with open(template_file, "r", encoding="utf-8") as f:
        content = f.read()

    patterns = [
        r'class=["\']([^"\']+)["\']',
        r'class:\s*["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, content):
            class_string = match.group(1)
            for cls in class_string.split():
                if cls and re.match(r"^[a-zA-Z_][a-zA-Z0-9_-]*$", cls):
                    classes.append(cls)

    return classes


def scan_templates(templates_dir: Path) -> Tuple[Counter, Set[Path]]:
    """Scan tous les templates et compte l'utilisation des classes."""
    class_usage = Counter()
    template_files = set()

    for template_file in templates_dir.rglob("*.html"):
        template_files.add(template_file)
        classes = extract_template_classes(template_file)
        class_usage.update(classes)

    return class_usage, template_files


def analyze_css_usage(css_dir: Path, templates_dir: Path) -> Dict[str, any]:
    """Analyse l'utilisation des classes CSS."""
    all_css_classes, classes_by_file = extract_all_css_classes(css_dir)
    class_usage, template_files = scan_templates(templates_dir)

    # Filtrer les classes exclues de l'analyse
    filtered_class_usage = Counter(
        {cls: count for cls, count in class_usage.items() if not is_excluded_class(cls)}
    )

    used_classes = set(filtered_class_usage.keys())
    unused_classes = all_css_classes - used_classes

    unused_by_file = {}
    for filename, file_classes in classes_by_file.items():
        unused_by_file[filename] = file_classes - used_classes

    rarely_used = {
        cls: count
        for cls, count in filtered_class_usage.items()
        if count <= 3 and cls in all_css_classes
    }

    undefined_classes = {
        cls for cls in filtered_class_usage.keys() if cls not in all_css_classes
    }

    excluded_classes = {
        cls: count for cls, count in class_usage.items() if is_excluded_class(cls)
    }

    return {
        "total_css_classes": len(all_css_classes),
        "total_used_classes": len(used_classes),
        "total_templates": len(template_files),
        "unused_classes": sorted(unused_classes),
        "unused_by_file": unused_by_file,
        "rarely_used": rarely_used,
        "undefined_classes": sorted(undefined_classes),
        "excluded_classes": excluded_classes,
        "class_usage": filtered_class_usage,
        "classes_by_file": classes_by_file,
        "css_files_analyzed": sorted(classes_by_file.keys()),
    }


def print_report(analysis: Dict[str, any]):
    """Affiche un rapport détaillé de l'analyse."""
    print("=" * 80)
    print("RAPPORT D'ANALYSE DES CLASSES CSS")
    print("=" * 80)
    print()

    print(f"📁 Fichiers CSS analysés ({len(analysis['css_files_analyzed'])}):")
    for filename in analysis["css_files_analyzed"]:
        count = len(analysis["classes_by_file"][filename])
        print(f"  • {filename}: {count} classes")
    print()

    if analysis["excluded_classes"]:
        print(f"🚫 Classes exclues de l'analyse ({len(analysis['excluded_classes'])}):")
        most_common_excluded = sorted(
            analysis["excluded_classes"].items(), key=lambda x: x[1], reverse=True
        )[:10]
        for cls, count in most_common_excluded:
            print(f"  • .{cls}: {count} fois")
        if len(analysis["excluded_classes"]) > 10:
            print(f"  ... et {len(analysis['excluded_classes']) - 10} autres")
        print()

    print(f"📊 Statistiques générales:")
    print(f"  • Nombre total de classes CSS définies: {analysis['total_css_classes']}")
    print(f"  • Nombre de classes utilisées: {analysis['total_used_classes']}")
    print(f"  • Nombre de templates analysés: {analysis['total_templates']}")
    if analysis["total_css_classes"] > 0:
        usage_rate = (
            analysis["total_used_classes"] / analysis["total_css_classes"]
        ) * 100
        print(f"  • Taux d'utilisation: {usage_rate:.1f}%")
    print()

    print(f"❌ Classes inutilisées par fichier:")
    for filename in sorted(analysis["unused_by_file"].keys()):
        unused = analysis["unused_by_file"][filename]
        if unused:
            print(f"\n  {filename} ({len(unused)} classes):")
            for cls in sorted(unused):
                print(f"    • .{cls}")
    print()

    print(f"❌ Total des classes inutilisées ({len(analysis['unused_classes'])}):")
    if analysis["unused_classes"]:
        for cls in analysis["unused_classes"]:
            print(f"  • .{cls}")
    else:
        print("  ✅ Toutes les classes sont utilisées !")
    print()

    print(f"⚠️  Classes rarement utilisées (≤ 3 fois) ({len(analysis['rarely_used'])}):")
    if analysis["rarely_used"]:
        for cls, count in sorted(analysis["rarely_used"].items(), key=lambda x: x[1]):
            print(f"  • .{cls}: {count} fois")
    else:
        print("  ✅ Aucune classe rarement utilisée")
    print()

    if analysis["undefined_classes"]:
        print(
            f"⚠️  Classes utilisées mais non définies ({len(analysis['undefined_classes'])}):"
        )
        print(
            "  (Probablement des classes externes: Bootstrap, Font Awesome, Flatpickr, etc.)"
        )
        for cls in analysis["undefined_classes"]:
            count = analysis["class_usage"][cls]
            print(f"  • .{cls}: {count} fois")
        print()

    print("🏆 Top 10 des classes les plus utilisées:")
    most_common = analysis["class_usage"].most_common(10)
    for cls, count in most_common:
        status = (
            "✅"
            if cls
            in {c for classes in analysis["classes_by_file"].values() for c in classes}
            else "⚠️"
        )
        print(f"  {status} .{cls}: {count} fois")
    print()

    print("=" * 80)


def save_report_to_file(analysis: Dict[str, any], output_file: Path):
    """Sauvegarde le rapport dans un fichier texte."""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("RAPPORT D'ANALYSE DES CLASSES CSS\n")
        f.write("=" * 80 + "\n\n")

        f.write("FICHIERS CSS ANALYSÉS:\n")
        for filename in sorted(analysis["css_files_analyzed"]):
            count = len(analysis["classes_by_file"][filename])
            f.write(f"  • {filename}: {count} classes\n")
        f.write("\n")

        if analysis["excluded_classes"]:
            f.write(
                f"CLASSES EXCLUES DE L'ANALYSE ({len(analysis['excluded_classes'])}):\n"
            )
            for cls, count in sorted(
                analysis["excluded_classes"].items(), key=lambda x: x[1], reverse=True
            ):
                f.write(f"  • .{cls}: {count} fois\n")
            f.write("\n")

        f.write("CLASSES INUTILISÉES PAR FICHIER:\n")
        for filename in sorted(analysis["unused_by_file"].keys()):
            unused = analysis["unused_by_file"][filename]
            if unused:
                f.write(f"\n  {filename} ({len(unused)} classes):\n")
                for cls in sorted(unused):
                    f.write(f"    • .{cls}\n")
        f.write("\n")

        f.write("CLASSES RAREMENT UTILISÉES (≤ 3 fois):\n")
        for cls, count in sorted(analysis["rarely_used"].items(), key=lambda x: x[1]):
            f.write(f"  • .{cls}: {count} fois\n")
        f.write("\n")

        if analysis["undefined_classes"]:
            f.write("CLASSES UTILISÉES MAIS NON DÉFINIES:\n")
            for cls in analysis["undefined_classes"]:
                count = analysis["class_usage"][cls]
                f.write(f"  • .{cls}: {count} fois\n")
            f.write("\n")


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    CSS_DIR = BASE_DIR / "static" / "css"
    TEMPLATES_DIR = BASE_DIR / "templates"
    OUTPUT_FILE = BASE_DIR / "css_analysis_report.txt"

    print("🔍 Analyse en cours...")
    print(f"  CSS directory: {CSS_DIR}")
    print(f"  Templates: {TEMPLATES_DIR}")
    print(f"  Patterns exclus: {', '.join(EXCLUDED_CLASS_PATTERNS)}")
    print()

    analysis = analyze_css_usage(CSS_DIR, TEMPLATES_DIR)
    print_report(analysis)
    save_report_to_file(analysis, OUTPUT_FILE)
    print(f"💾 Rapport sauvegardé dans: {OUTPUT_FILE}")
