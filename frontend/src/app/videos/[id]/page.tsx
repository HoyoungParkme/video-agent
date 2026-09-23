/** /videos/{id} → UI-4 결과 */
import Result from "@/screens/Result";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <Result id={Number(id)} />;
}
