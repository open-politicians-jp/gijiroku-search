import { redirect } from 'next/navigation';

interface ManifestoSlugPageProps {
  params: { slug: string };
}

const MANIFESTO_SLUGS = [
  'genzei-nihon',
  'jiyuminshuto',
  'kakuyugo-to',
  'kokka-seishin-kai',
  'kokuminminshuto',
  'kokusei-governance',
  'komeito',
  'kyosanto',
  'nhk-to',
  'nihon-hoshu-to',
  'nihon-kaikaku-to',
  'nihon-katei-mamoru-kai',
  'nipponishin',
  'reiwa',
  'rikkenminshuto',
  'saisei-no-michi',
  'sanseito',
  'shakai-minshu-to',
  'shinto-kunimori',
  'shinto-yamato',
  'team-mirai',
  'teammirai',
  'zeikin-tomei-ka-to'
];

export function generateStaticParams() {
  return MANIFESTO_SLUGS.map((slug) => ({ slug }));
}

export default function ManifestoSlugPage({ params }: ManifestoSlugPageProps) {
  redirect(`/manifestos/llm/${params.slug}`);
}
