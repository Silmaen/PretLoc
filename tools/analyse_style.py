"""
Script d'analyse de cohérence du style CSS dans les templates Django.
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def extract_component_patterns(template_file: Path) -> Dict[str, List[str]]:
    """Extrait les patterns de composants (boutons, cartes, formulaires, etc.)."""
    with open(template_file, "r", encoding="utf-8") as f:
        content = f.read()

    patterns = {
        "buttons": re.findall(r'<button[^>]*class=["\']([^"\']*)["\']', content),
        "cards": re.findall(r'<div[^>]*class=["\']([^"\']*card[^"\']*)["\']', content),
        "forms": re.findall(r'<form[^>]*class=["\']([^"\']*)["\']', content),
        "inputs": re.findall(r'<input[^>]*class=["\']([^"\']*)["\']', content),
        "tables": re.findall(r'<table[^>]*class=["\']([^"\']*)["\']', content),
        "badges": re.findall(r'class=["\']([^"\']*badge[^"\']*)["\']', content),
        "headers": re.findall(r'<h[1-6][^>]*class=["\']([^"\']*)["\']', content),
    }

    return patterns


def analyze_style_consistency(templates_dir: Path) -> Dict[str, any]:
    """Analyse la cohérence du style à travers tous les templates."""

    component_usage = defaultdict(lambda: defaultdict(list))

    for template_file in templates_dir.rglob("*.html"):
        patterns = extract_component_patterns(template_file)

        for component_type, class_lists in patterns.items():
            for class_list in class_lists:
                classes = class_list.split()
                component_usage[component_type][tuple(sorted(classes))].append(
                    template_file.relative_to(templates_dir)
                )

    return component_usage


def find_inconsistencies(component_usage: Dict) -> Dict[str, List]:
    """Identifie les incohérences dans l'utilisation des composants."""

    inconsistencies = {}

    for component_type, class_patterns in component_usage.items():
        if len(class_patterns) > 3:  # Si plus de 3 variantes différentes
            inconsistencies[component_type] = {
                "patterns": dict(class_patterns),
                "count": len(class_patterns),
            }

    return inconsistencies


def suggest_harmonization(component_usage: Dict) -> Dict[str, Dict]:
    """Suggère une harmonisation basée sur les patterns les plus utilisés."""

    suggestions = {}

    for component_type, class_patterns in component_usage.items():
        # Trouve le pattern le plus utilisé
        most_common = max(class_patterns.items(), key=lambda x: len(x[1]))
        pattern, files = most_common

        suggestions[component_type] = {
            "recommended": " ".join(pattern),
            "usage_count": len(files),
            "alternatives": {
                " ".join(p): len(f) for p, f in class_patterns.items() if p != pattern
            },
        }

    return suggestions


def print_consistency_report(
    component_usage: Dict, inconsistencies: Dict, suggestions: Dict
):
    """Affiche un rapport de cohérence du style."""

    print("=" * 80)
    print("RAPPORT D'HARMONISATION DU STYLE")
    print("=" * 80)
    print()

    # Vue d'ensemble
    print("📊 Vue d'ensemble des composants:")
    for component_type, patterns in component_usage.items():
        total_usage = sum(len(files) for files in patterns.values())
        print(
            f"  • {component_type}: {len(patterns)} variantes, {total_usage} utilisations"
        )
    print()

    # Incohérences détectées
    if inconsistencies:
        print("⚠️  INCOHÉRENCES DÉTECTÉES:")
        print()

        for component_type, data in inconsistencies.items():
            print(
                f"  🔴 {component_type.upper()} ({data['count']} variantes différentes):"
            )

            # Trier par nombre d'utilisations
            sorted_patterns = sorted(
                data["patterns"].items(), key=lambda x: len(x[1]), reverse=True
            )

            for pattern, files in sorted_patterns:
                class_str = " ".join(pattern) if pattern else "(aucune classe)"
                print(f"    • '{class_str}': {len(files)} fois")
                for file in files[:3]:  # Montre 3 exemples
                    print(f"      - {file}")
                if len(files) > 3:
                    print(f"      ... et {len(files) - 3} autres")
            print()
    else:
        print("✅ Aucune incohérence majeure détectée!")
        print()

    # Suggestions d'harmonisation
    print("💡 SUGGESTIONS D'HARMONISATION:")
    print()

    for component_type, suggestion in suggestions.items():
        if suggestion["alternatives"]:
            print(f"  📌 {component_type.upper()}:")
            print(f"    Pattern recommandé: '{suggestion['recommended']}'")
            print(f"    Utilisé {suggestion['usage_count']} fois")

            if suggestion["alternatives"]:
                print(f"    Patterns à remplacer:")
                for alt_pattern, count in suggestion["alternatives"].items():
                    alt_str = alt_pattern if alt_pattern else "(aucune classe)"
                    print(f"      • '{alt_str}': {count} fois")
            print()


def generate_refactoring_script(
    component_usage: Dict, suggestions: Dict, output_file: Path
):
    """Génère un script de refactoring pour harmoniser le style."""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Script de refactoring pour harmoniser le style\n\n")
        f.write("# Commandes de remplacement (à exécuter manuellement)\n\n")

        for component_type, suggestion in suggestions.items():
            if suggestion["alternatives"]:
                f.write(f"# {component_type.upper()}\n")
                f.write(f"# Pattern recommandé: {suggestion['recommended']}\n\n")

                for alt_pattern, count in suggestion["alternatives"].items():
                    if alt_pattern:
                        f.write(
                            f"# Remplacer '{alt_pattern}' par '{suggestion['recommended']}'\n"
                        )
                        f.write(f"# (utilisé {count} fois)\n\n")


def analyze_button_patterns(templates_dir: Path) -> Dict:
    """Analyse spécifique des patterns de boutons."""

    button_patterns = {
        "primary_actions": [],  # Boutons d'action principale
        "secondary_actions": [],  # Boutons secondaires
        "danger_actions": [],  # Boutons de suppression
        "form_buttons": [],  # Boutons de formulaire
    }

    for template_file in templates_dir.rglob("*.html"):
        with open(template_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Boutons primaires (submit, ajouter, valider)
        primary = re.findall(
            r'<button[^>]*(?:type="submit"|>(?:Ajouter|Créer|Valider|Enregistrer))[^>]*class=["\']([^"\']*)["\']',
            content,
            re.IGNORECASE,
        )
        button_patterns["primary_actions"].extend(primary)

        # Boutons de suppression
        danger = re.findall(
            r'<(?:button|a)[^>]*(?:delete|supprimer|confirm)[^>]*class=["\']([^"\']*)["\']',
            content,
            re.IGNORECASE,
        )
        button_patterns["danger_actions"].extend(danger)

    return button_patterns


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    TEMPLATES_DIR = BASE_DIR / "templates"
    OUTPUT_FILE = BASE_DIR / "style_harmonization_refactoring.txt"

    print("🔍 Analyse de la cohérence du style...")
    print(f"  Templates: {TEMPLATES_DIR}")
    print()

    # Analyse générale
    component_usage = analyze_style_consistency(TEMPLATES_DIR)
    inconsistencies = find_inconsistencies(component_usage)
    suggestions = suggest_harmonization(component_usage)

    # Rapport
    print_consistency_report(component_usage, inconsistencies, suggestions)

    # Script de refactoring
    generate_refactoring_script(component_usage, suggestions, OUTPUT_FILE)
    print(f"💾 Script de refactoring sauvegardé dans: {OUTPUT_FILE}")
    print()

    # Analyse spécifique des boutons
    print("🔍 Analyse détaillée des boutons...")
    button_patterns = analyze_button_patterns(TEMPLATES_DIR)

    print("\n📊 Patterns de boutons détectés:")
    for btn_type, patterns in button_patterns.items():
        unique_patterns = set(patterns)
        print(f"  • {btn_type}: {len(unique_patterns)} variantes")
