import React from 'react';

import { useZenodoUserProfile } from '../core';

export const ZenodoUserProfile: React.FC = () => {
  const { profile, error } = useZenodoUserProfile();

  if (profile === null) {
    return <div>{error ? <p>{error}</p> : null}</div>;
  }

  return (
    <div>
      <p>
        Zenodo user: <strong>{profile.email}</strong>
      </p>
    </div>
  );
};
