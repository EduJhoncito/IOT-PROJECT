from typing import Optional


class SensorDataRouter:
    """
    Routes models to the appropriate database:
    - core.Sensor, core.SensorReading -> 'historical'
    - core.RealtimeReading -> 'cache'
    - auth/admin/contenttypes/sessions -> 'historical' (default)
    """

    app_label_core = 'core'

    def db_for_read(self, model, **hints) -> Optional[str]:
        if model._meta.app_label == self.app_label_core:
            if model.__name__ == 'RealtimeReading':
                return 'cache'
            return 'historical'
        return None

    def db_for_write(self, model, **hints) -> Optional[str]:
        if model._meta.app_label == self.app_label_core:
            if model.__name__ == 'RealtimeReading':
                return 'cache'
            return 'historical'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        db_list = {'historical', 'cache'}
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label_core:
            if model_name == 'realtimereading':
                return db == 'cache'
            # Sensor and SensorReading
            return db == 'historical'

        # Django built-ins to historical by default
        if app_label in {'auth', 'admin', 'contenttypes', 'sessions'}:
            return db == 'historical'

        return None

