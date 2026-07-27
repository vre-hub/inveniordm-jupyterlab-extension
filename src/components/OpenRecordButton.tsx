import React from 'react';

type ZenodoRecordLink = {
  links: {
    self_html: string;
  };
};

/**
 * A button that opens a Zenodo record in a new tab.
 */
export function OpenRecordButton({
  record,
  text
}: {
  record: ZenodoRecordLink;
  text: string;
}): JSX.Element {
  const url = record.links.self_html;
  return <OpenLinkButton url={url} text={text} />;
}

function OpenLinkButton({
  url,
  text
}: {
  url: string;
  text: string;
}): JSX.Element {
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const openLink = async (): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      window.open(url, '_blank');
    } catch (reason) {
      setError(String(reason));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <button
        disabled={isLoading}
        onClick={() => void openLink()}
        type="button"
      >
        {isLoading ? 'Opening...' : text}
      </button>
      {error ? <span>{error}</span> : null}
    </>
  );
}
