import { Later } from "@/components/layout/Later";

export default function Page({ params }: { params: Promise<{ locale: string }> }) {
  return <Later params={params} phase="6.5" back="" />;
}
