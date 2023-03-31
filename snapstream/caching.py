"""Snapstream caching."""

from functools import partial
from os import cpu_count, path
from typing import Any

from rocksdict import (AccessType, DBCompactionStyle, DBCompressionType,
                       FifoCompactOptions, Options, Rdict)

MB, MINUTES = 1024 * 1024, 60


class Cache:
    """A Rocksdb instance."""

    def __init__(
        self,
        name,
        options=None,
        access_type=AccessType.with_ttl(4 * 24 * 60 * MINUTES),
        target_table_size=25 * MB
    ) -> None:
        """Create instance that holds rocksdb reference.

        This configuration setup optimizes for low disk usage (25mb per cf)
        per LocalTable. When 25mb (target_column_family_size) is reached,
        the oldest file gets deleted (the first records go out).

        TTL is set to 4 days, older records may be removed during compaction.
        Whenever a new column family is created using the `.partition()`
        function, previously created cf's are deleted
        if max_column_families is set.

        Some entries below may be ignored because they apply to lvl1 files.
        When fifo compaction is replaced, these entries are good defaults.
        """
        self.name = name
        options = options or self._default_options(target_table_size)
        column_families = {
            key: options
            for key in Rdict.list_cf(name, options)
        } if path.exists(name + '/CURRENT') else {}
        self.db = Rdict(name, options, column_families, access_type)

    @staticmethod
    def _default_options(target_table_size: int):
        options = Options()
        compaction_options = FifoCompactOptions()
        compaction_options.max_table_files_size = target_table_size
        options.create_if_missing(True)
        options.set_max_background_jobs(cpu_count() or 2)
        options.increase_parallelism(cpu_count() or 2)
        options.set_log_file_time_to_roll(30 * MINUTES)
        options.set_keep_log_file_num(1)
        options.set_max_log_file_size(int(0.1 * MB))
        options.set_fifo_compaction_options(compaction_options)
        options.set_compaction_style(DBCompactionStyle.fifo())
        options.set_level_zero_file_num_compaction_trigger(4)
        options.set_level_zero_slowdown_writes_trigger(6)
        options.set_level_zero_stop_writes_trigger(8)
        options.set_max_write_buffer_number(2)
        options.set_write_buffer_size(1 * MB)
        options.set_target_file_size_base(256 * MB)
        options.set_max_bytes_for_level_base(1024 * MB)
        options.set_max_bytes_for_level_multiplier(4.0)
        options.set_compression_type(DBCompressionType.lz4())
        options.set_delete_obsolete_files_period_micros(10 * 1000)
        return options

    def __call__(self, key, val, *args) -> None:
        """Call cache to set item."""
        self.__setitem__(key, val)

    def __contains__(self, key) -> bool:
        """Key exists in db."""
        return key in self.db

    def __delitem__(self, key) -> None:
        """Delete item from db."""
        del self.db[key]

    def __getitem__(self, key) -> Any:
        """Get item from db or None."""
        try:
            return self.db[key]
        except KeyError:
            pass

    def __setitem__(self, key, val) -> None:
        """Set item in db."""
        self.db[key] = val

    def __enter__(self) -> Rdict:
        """Contextmanager."""
        return self.db.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit contextmanager."""
        self.db.__exit__(exc_type, exc_val, exc_tb)

    def __getattr__(self, attr):
        """Redirect to Rdict."""
        return partial(getattr(Rdict, attr), self.db)
