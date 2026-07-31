type PublicKeyCredentialDescriptorJSON = Omit<PublicKeyCredentialDescriptor, "id"> & {
  id: string;
};

type PublicKeyCredentialUserEntityJSON = Omit<PublicKeyCredentialUserEntity, "id"> & {
  id: string;
};

type PublicKeyCredentialCreationOptionsJSON = Omit<
  PublicKeyCredentialCreationOptions,
  "challenge" | "user" | "excludeCredentials"
> & {
  challenge: string;
  user: PublicKeyCredentialUserEntityJSON;
  excludeCredentials?: PublicKeyCredentialDescriptorJSON[];
};

type PublicKeyCredentialRequestOptionsJSON = Omit<
  PublicKeyCredentialRequestOptions,
  "challenge" | "allowCredentials"
> & {
  challenge: string;
  allowCredentials?: PublicKeyCredentialDescriptorJSON[];
};
