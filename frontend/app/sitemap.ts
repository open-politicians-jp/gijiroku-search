import type { MetadataRoute } from 'next';
import fs from 'fs';
import path from 'path';

const SITE_URL = 'https://open-politicians-jp.github.io/gijiroku-search';

const staticRoutes = [
  '/',
  '/about',
  '/archive',
  '/legislators',
  '/manifestos',
  '/manifestos/llm',
  '/sangiin',
  '/sangiin-comparison',
  '/shugiin-manifestos',
  '/shugiin-comparison',
  '/shugiin-candidates',
  '/summaries',
];

const getManifestoLlms = () => {
  const dir = path.join(process.cwd(), 'app', 'manifestos', 'llm');
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => `/manifestos/llm/${entry.name}`);
};

const shugiinSlugMap: Record<string, string> = {
  '自由民主党': 'jiyuminshuto',
  '中道改革連合': 'chudokaikakuren',
  '日本維新の会': 'nipponishin',
  '参政党': 'sanseito',
  '国民民主党': 'kokuminminshuto',
  'れいわ新選組': 'reiwa',
  '日本共産党': 'kyosanto',
};

const getShugiinManifestos = () => {
  const dataPath = path.join(process.cwd(), 'public', 'data', 'shugiin_policy_summaries.json');
  if (!fs.existsSync(dataPath)) return [];
  const raw = fs.readFileSync(dataPath, 'utf-8');
  const data = JSON.parse(raw);
  const slugs = (data.parties || [])
    .map((party: { name: string }) => shugiinSlugMap[party.name])
    .filter(Boolean);
  return slugs.map((slug: string) => `/shugiin-manifestos/${slug}`);
};

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  const routes = [
    ...staticRoutes,
    ...getManifestoLlms(),
    ...getShugiinManifestos(),
  ];

  return routes.map((route) => ({
    url: `${SITE_URL}${route}`,
    lastModified,
    changeFrequency: 'weekly',
    priority: route === '/' ? 1 : 0.7,
  }));
}
