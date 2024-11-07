from rope.base.project import Project
from rope.refactor.importutils import ImportOrganizer


# Инициализируем проект в директории
project = Project('/Users/sakhnov/Work/com_project/community_platform')
organizer = ImportOrganizer(project)

# Находим и преобразуем импорты
for file in project.get_files():
    if file.path.endswith('.py'):
        try:
            # Применяем рефакторинг к каждому Python-файлу
            changes = organizer.organize_imports(file)
            if changes:
                project.do(changes)
        except Exception as e:
            print(f"Error processing {file.path}: {e}")

# Закрываем проект
project.close()