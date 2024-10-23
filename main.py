import os
import psutil
import shutil
import time
import hashlib
import json
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich import box
from rich.panel import Panel

console = Console()

def list_drives():
    partitions = psutil.disk_partitions()
    drives = [part.device for part in partitions]
    return drives

def get_disk_usage(drive):
    disk_info = shutil.disk_usage(drive)
    total = disk_info.total // (1024 ** 3)
    used = disk_info.used // (1024 ** 3)
    free = disk_info.free // (1024 ** 3)
    percent_used = (used / total) * 100
    return total, used, free, percent_used

def analyze_by_file_type(directory):
    file_types = {}
    for foldername, subfolders, filenames in os.walk(directory):
        for filename in filenames:
            file_ext = os.path.splitext(filename)[1].lower()
            filepath = os.path.join(foldername, filename)
            try:
                size = os.path.getsize(filepath)
                if file_ext in file_types:
                    file_types[file_ext] += size
                else:
                    file_types[file_ext] = size
            except (FileNotFoundError, PermissionError):
                continue
    sorted_file_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
    return sorted_file_types

def get_file_hash(filepath):
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
    except (FileNotFoundError, PermissionError):
        return None
    return hasher.hexdigest()

def find_duplicate_files(directory):
    hash_map = {}
    duplicates = []
    for foldername, subfolders, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(foldername, filename)
            file_hash = get_file_hash(filepath)
            if file_hash:
                if file_hash in hash_map:
                    duplicates.append((filepath, hash_map[file_hash]))
                else:
                    hash_map[file_hash] = filepath
    return duplicates

def find_large_files(directory, size_limit=1 * (1024 ** 3)):
    large_files = []
    for foldername, subfolders, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(foldername, filename)
            try:
                size = os.path.getsize(filepath)
                if size > size_limit:
                    large_files.append((filepath, size))
            except (FileNotFoundError, PermissionError):
                continue
    return sorted(large_files, key=lambda x: x[1], reverse=True)

def clean_temp_files(temp_dirs):
    cleaned_size = 0
    for temp_dir in temp_dirs:
        for foldername, subfolders, filenames in os.walk(temp_dir):
            for filename in filenames:
                filepath = os.path.join(foldername, filename)
                try:
                    file_size = os.path.getsize(filepath)
                    os.remove(filepath)
                    cleaned_size += file_size
                except (FileNotFoundError, PermissionError):
                    continue
    return cleaned_size

def monitor_disk_usage(drive, threshold=90):
    console.print(f"[bold cyan]Iniciando monitoreo del disco {drive}... Presiona Ctrl+C para detener.[/bold cyan]")
    try:
        while True:
            total, used, free, percent_used = get_disk_usage(drive)
            console.print(f"[bold yellow]Espacio usado: {percent_used:.2f}%[/bold yellow]")
            if percent_used > threshold:
                console.print(f"[bold red]Advertencia: El uso del disco ha superado el {threshold}%![/bold red]")
            time.sleep(10)
    except KeyboardInterrupt:
        console.print("\n[bold green]Monitoreo detenido por el usuario.[/bold green]")

def save_analysis(analysis_data, file_name="disk_analysis_history.json"):
    try:
        with open(file_name, 'a') as f:
            json.dump(analysis_data, f)
            f.write("\n")
    except IOError:
        console.print("[bold red]Error al guardar el análisis en el archivo.[/bold red]")

def load_analysis_history(file_name="disk_analysis_history.json"):
    history = []
    try:
        with open(file_name, 'r') as f:
            for line in f:
                history.append(json.loads(line))
    except FileNotFoundError:
        console.print("[bold yellow]No se ha encontrado historial previo.[/bold yellow]")
    return history

def show_options():
    console.print("\n[bold magenta]Opciones disponibles:[/bold magenta]")
    options_table = Table(title="Opciones", box=box.SIMPLE)
    options_table.add_column("Número", justify="right", style="bold yellow")
    options_table.add_column("Descripción", justify="left", style="bold green")
    options_table.add_row("1", "Análisis por tipo de archivo")
    options_table.add_row("2", "Buscar archivos duplicados")
    options_table.add_row("3", "Buscar archivos grandes")
    options_table.add_row("4", "Limpiar archivos temporales")
    options_table.add_row("5", "Monitorear el uso del disco")
    options_table.add_row("6", "Ver historial de análisis")
    options_table.add_row("7", "Salir")
    console.print(options_table)

def handle_option(selected_drive):
    while True:
        show_options()
        try:
            option = int(console.input("\n[bold cyan]Selecciona una opción: [/bold cyan]"))
        except ValueError:
            console.print("[bold red]Selección inválida. Inténtalo de nuevo.[/bold red]")
            continue

        if option == 1:
            console.print("[bold cyan]Analizando por tipo de archivo...[/bold cyan]")
            file_types = analyze_by_file_type(selected_drive)
            if file_types:
                file_type_table = Table(title="Tipos de Archivo", box=box.SIMPLE)
                file_type_table.add_column("Extensión", style="bold green")
                file_type_table.add_column("Tamaño (GB)", justify="right", style="bold yellow")
                for ext, size in file_types:
                    size_in_gb = size / (1024 ** 3)
                    file_type_table.add_row(ext, f"{size_in_gb:.2f} GB")
                console.print(file_type_table)
            else:
                console.print("[bold red]No se encontraron archivos en el disco.[/bold red]")
        elif option == 2:
            console.print("[bold cyan]Buscando archivos duplicados...[/bold cyan]")
            duplicates = find_duplicate_files(selected_drive)
            if duplicates:
                duplicate_table = Table(title="Archivos Duplicados", box=box.SIMPLE)
                duplicate_table.add_column("Archivo", style="bold green")
                duplicate_table.add_column("Duplicado", style="bold red")
                for file1, file2 in duplicates:
                    duplicate_table.add_row(file1, file2)
                console.print(duplicate_table)
            else:
                console.print("[bold red]No se encontraron archivos duplicados.[/bold red]")
        elif option == 3:
            console.print("[bold cyan]Buscando archivos grandes...[/bold cyan]")
            large_files = find_large_files(selected_drive)
            if large_files:
                large_files_table = Table(title="Archivos Grandes", box=box.SIMPLE)
                large_files_table.add_column("Archivo", style="bold green")
                large_files_table.add_column("Tamaño (GB)", justify="right", style="bold yellow")
                for file, size in large_files:
                    size_in_gb = size / (1024 ** 3)
                    large_files_table.add_row(file, f"{size_in_gb:.2f} GB")
                console.print(large_files_table)
            else:
                console.print("[bold red]No se encontraron archivos grandes.[/bold red]")
        elif option == 4:
            console.print("[bold cyan]Limpiando archivos temporales...[/bold cyan]")
            temp_dirs = ["C:/Windows/Temp", "/tmp"]
            cleaned_size = clean_temp_files(temp_dirs)
            cleaned_size_in_gb = cleaned_size / (1024 ** 3)
            console.print(f"[bold green]Se han limpiado {cleaned_size_in_gb:.2f} GB de archivos temporales.[/bold green]")
        elif option == 5:
            console.print("[bold cyan]Iniciando monitoreo del disco...[/bold cyan]")
            monitor_disk_usage(selected_drive)
        elif option == 6:
            console.print("[bold cyan]Cargando historial de análisis...[/bold cyan]")
            history = load_analysis_history()
            if history:
                history_table = Table(title="Historial de Análisis", box=box.SIMPLE)
                history_table.add_column("Fecha", style="bold green")
                history_table.add_column("Disco", style="bold cyan")
                history_table.add_column("Espacio Usado (%)", justify="right", style="bold yellow")
                for record in history:
                    history_table.add_row(record['date'], record['drive'], f"{record['percent_used']:.2f}%")
                console.print(history_table)
            else:
                console.print("[bold yellow]No hay análisis previos guardados.[/bold yellow]")
        elif option == 7:
            console.print("[bold green]Saliendo del programa...[/bold green]")
            break
        else:
            console.print("[bold red]Selección inválida. Inténtalo de nuevo.[/bold red]")

def main():
    console.clear()
    console.print(Panel("Analizador de Disco - Terminal UI", style="bold cyan"))

    drives = list_drives()
    console.print("\n[bold magenta]Discos Disponibles:[/bold magenta]")
    
    drive_table = Table(title="Discos Disponibles", box=box.SIMPLE)
    drive_table.add_column("N°", justify="right", style="bold yellow")
    drive_table.add_column("Unidad", justify="center", style="bold green")

    for idx, drive in enumerate(drives):
        drive_table.add_row(str(idx + 1), drive)

    console.print(drive_table)

    try:
        drive_selection = int(console.input("\n[bold cyan]Selecciona el número del disco a analizar: [/bold cyan]")) - 1
        if drive_selection < 0 or drive_selection >= len(drives):
            raise ValueError
    except ValueError:
        console.print("[bold red]Selección inválida. Saliendo del programa...[/bold red]")
        return
    
    selected_drive = drives[drive_selection]

    total, used, free, percent_used = get_disk_usage(selected_drive)

    console.print(f"\n[bold cyan]Análisis del disco:[/bold cyan] [bold green]{selected_drive}[/bold green]\n")
    info_table = Table(title="Información del Disco", box=box.SIMPLE)
    info_table.add_column("Descripción", style="bold yellow")
    info_table.add_column("Valor", justify="right", style="bold white")
    
    info_table.add_row("Espacio total", f"{total} GB")
    info_table.add_row("Espacio usado", f"{used} GB")
    info_table.add_row("Espacio libre", f"{free} GB")
    info_table.add_row("Porcentaje usado", f"{percent_used:.2f}%")
    
    disk_info = psutil.disk_partitions()
    for partition in disk_info:
        if partition.device == selected_drive:
            info_table.add_row("Sistema de archivos", partition.fstype)
            break

    console.print(info_table)

    console.print("\n[bold magenta]Uso del disco:[/bold magenta]")
    with Progress() as progress:
        task = progress.add_task("Uso del disco", total=100)
        progress.update(task, completed=percent_used)

    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    analysis_data = {
        "date": current_time,
        "drive": selected_drive,
        "percent_used": percent_used
    }
    save_analysis(analysis_data)

    handle_option(selected_drive)

if __name__ == "__main__":
    main()
