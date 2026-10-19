import subprocess
import sys

scripts = [
    "scripts/0run_agua_util_P_CN_V2.py",
    "scripts/1resumen_AguaUtil_depto_P_CNV2.py",
    "scripts/2_0_proc_final_P_CN_V1.py",
    "scripts/2_1proc_final_P_CN_V3.py",
    # "scripts/calcular_anomalias_P_CN.py",
    "scripts/calcular_anomalias_P_CN_promedio_desvio_v4.py",
    "scripts/generar_gpkg_anomalias_P_CN_v2.py"
]

for script in scripts:
    print(f"Ejecutando: {script}")
    resultado = subprocess.run(["py", script])
    if resultado.returncode != 0:
        print(f"❌ Falló {script}. Deteniendo ejecución.")
        sys.exit(1)
    else:
        print(f"✅ {script} completado correctamente.")