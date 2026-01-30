import { redirect } from 'next/navigation';

interface ManifestoSlugPageProps {
  params: { slug: string };
}

export default function ManifestoSlugPage({ params }: ManifestoSlugPageProps) {
  redirect(`/manifestos/llm/${params.slug}`);
}
