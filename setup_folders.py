# setup_folders.py
import os

# Estructura de carpetas y archivos
structure = {
    'utils': [
        '__init__.py',
        'data_loader.py',
        'data_processor.py',
        'formatters.py',
        'date_utils.py'
    ],
    'models': [
        '__init__.py',
        'forecast_engine.py',
        'fianzas_adjuster.py',
        'budget_2026.py'
    ],
    'components': [
        '__init__.py',
        'sidebar.py',
        'summary_cards.py',
        'tables.py',
        'charts.py'
    ]
}

# Crear carpetas y archivos
for folder, files in structure.items():
    # Crear carpeta
    os.makedirs(folder, exist_ok=True)
    print(f"📁 Carpeta creada: {folder}/")
    
    # Crear archivos vacíos
    for file in files:
        filepath = os.path.join(folder, file)
        open(filepath, 'a').close()
        print(f"   ✅ {file}")

print("\n🎉 ¡Todas las carpetas y archivos creados exitosamente!")
print("\n📋 Estructura creada:")
print("├── utils/ (5 archivos)")
print("├── models/ (4 archivos)")
print("└── components/ (5 archivos)")
