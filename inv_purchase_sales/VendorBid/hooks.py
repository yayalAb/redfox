def _relax_currency_rate_unique_constraint(cr):
    """Allow multiple res.currency.rate rows per day when exchange_rate_bank_id differs."""
    cr.execute(
        """
        ALTER TABLE res_currency_rate DROP CONSTRAINT IF EXISTS res_currency_rate_unique_name_per_day;
        """
    )
    cr.execute("DROP INDEX IF EXISTS res_currency_rate_unique_name_per_day_bank_null;")
    cr.execute("DROP INDEX IF EXISTS res_currency_rate_unique_name_per_day_bank_set;")
    cr.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS res_currency_rate_unique_name_per_day_bank_null
        ON res_currency_rate (name, currency_id, company_id)
        WHERE exchange_rate_bank_id IS NULL;
        """
    )
    cr.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS res_currency_rate_unique_name_per_day_bank_set
        ON res_currency_rate (name, currency_id, company_id, exchange_rate_bank_id)
        WHERE exchange_rate_bank_id IS NOT NULL;
        """
    )


def post_init_hook(env):
    _relax_currency_rate_unique_constraint(env.cr)
