from typing import Optional
import os


class SensorDataRouter:
    """
    Routes models to the appropriate database:
    - core.Sensor, core.SensorReading -> 'historical'
    - core.RealtimeReading -> 'cache'
    - auth/admin/contenttypes/sessions -> 'historical' (default)
    """

    app_label_core = 'core'
    single_db = os.getenv('SINGLE_DB', 'false').lower() == 'true'

    def db_for_read(self, model, **hints) -> Optional[str]:
        if model._meta.app_label == self.app_label_core:
            if model.__name__ == 'RealtimeReading':
                return 'historical' if self.single_db else 'cache'
            return 'historical'
        return None

    def db_for_write(self, model, **hints) -> Optional[str]:
        if model._meta.app_label == self.app_label_core:
            if model.__name__ == 'RealtimeReading':
                return 'historical' if self.single_db else 'cache'
            return 'historical'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        db_list = {'historical', 'cache'}
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Built-ins always on historical
        if app_label in {'auth', 'admin', 'contenttypes', 'sessions'}:
            return db == 'historical'

        if app_label == self.app_label_core:
            # In SINGLE_DB mode, migrate ALL core models on 'historical' only
            if self.single_db:
                return db == 'historical'

            # Multi-DB mode: split by model
            if model_name == 'realtimereading':
                return db == 'cache'
            return db == 'historical'

        return None
