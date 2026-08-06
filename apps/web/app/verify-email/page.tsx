import { redirect } from "next/navigation";

type Props = {
  searchParams: Promise<{ token?: string | string[] }>;
};

export default async function VerifyEmailPage({ searchParams }: Props) {
  const { token } = await searchParams;
  const value = Array.isArray(token) ? token[0] : token;
  if (!value || !/^[A-Za-z0-9_-]{20,512}$/.test(value)) redirect("/");
  redirect(`/?verify=${encodeURIComponent(value)}`);
}
