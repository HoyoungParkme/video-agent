/** /videos/{id}/progress → UI-3 분석 진행 */
import Progress from "@/screens/Progress";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <Progress id={Number(id)} />;
}
