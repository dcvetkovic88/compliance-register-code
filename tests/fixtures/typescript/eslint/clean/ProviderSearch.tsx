interface ProviderSearchProps {
  t: (key: string) => string;
}

export function ProviderSearch({ t }: ProviderSearchProps) {
  return (
    <div className="row" data-testid="provider-search">
      <input
        id="provider-search"
        className="row"
        type="text"
        placeholder={t("search.providers")}
        aria-label={t("search.label")}
      />
      <img src="/logo.svg" alt={t("brand.logo")} />
    </div>
  );
}
