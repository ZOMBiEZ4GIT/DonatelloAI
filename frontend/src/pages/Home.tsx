import { Link } from 'react-router-dom';
import { ImagePlus, Shield, Zap, DollarSign } from 'lucide-react';
import { useAuth } from '@/hooks';
import { ROUTES } from '@/utils/constants';

export const Home = () => {
  const { isAuthenticated } = useAuth();

  const features = [
    {
      icon: ImagePlus,
      title: 'Multi-Model AI',
      description: 'Access DALL-E 3, Stable Diffusion XL, Adobe Firefly, and Azure AI Image from one platform.',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'ISO 27001 compliant with comprehensive audit trails and data sovereignty.',
    },
    {
      icon: Zap,
      title: 'Intelligent Routing',
      description: 'Automatic model selection based on prompt complexity, cost, and quality requirements.',
    },
    {
      icon: DollarSign,
      title: 'Cost Management',
      description: 'Department budgets, real-time cost tracking, and intelligent cost optimization.',
    },
  ];

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-gradient-to-br from-primary-50 via-white to-purple-50">
      <div className="mx-auto max-w-7xl px-6 py-16">
        {/* Hero Section */}
        <div className="text-center">
          <h1 className="mb-6 text-5xl font-bold text-gray-900">
            Enterprise Image Generation Platform
          </h1>
          <p className="mx-auto mb-8 max-w-2xl text-xl text-gray-600">
            Secure, compliant, and cost-effective AI image generation for Australian enterprises.
            Multiple models, intelligent routing, and comprehensive governance.
          </p>
          <div className="flex justify-center gap-4">
            {!isAuthenticated && (
              <Link
                to={ROUTES.GENERATE}
                className="rounded-lg bg-primary-600 px-8 py-3 font-medium text-white transition-colors hover:bg-primary-700"
              >
                Get Started
              </Link>
            )}
            {isAuthenticated && (
              <Link
                to={ROUTES.GENERATE}
                className="rounded-lg bg-primary-600 px-8 py-3 font-medium text-white transition-colors hover:bg-primary-700"
              >
                Start Generating
              </Link>
            )}
            <a
              href="https://github.com"
              className="rounded-lg border-2 border-gray-300 px-8 py-3 font-medium text-gray-700 transition-colors hover:border-gray-400 hover:bg-gray-50"
            >
              Learn More
            </a>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-24 grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="rounded-lg border border-gray-200 bg-white p-6 shadow-soft transition-shadow hover:shadow-lg"
              >
                <div className="mb-4 inline-block rounded-lg bg-primary-100 p-3 text-primary-600">
                  <Icon size={24} />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-gray-900">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            );
          })}
        </div>

        {/* Stats Section */}
        <div className="mt-24 rounded-2xl bg-white p-12 shadow-soft">
          <div className="grid gap-8 md:grid-cols-3">
            <div className="text-center">
              <p className="text-4xl font-bold text-primary-600">99.95%</p>
              <p className="mt-2 text-gray-600">Uptime SLA</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-primary-600">4</p>
              <p className="mt-2 text-gray-600">AI Models</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-primary-600">ISO 27001</p>
              <p className="mt-2 text-gray-600">Compliant</p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-24 text-center">
          <h2 className="mb-4 text-3xl font-bold text-gray-900">
            Ready to transform your image generation workflow?
          </h2>
          <p className="mb-8 text-xl text-gray-600">
            Join leading Australian enterprises using our platform.
          </p>
          {!isAuthenticated && (
            <Link
              to={ROUTES.GENERATE}
              className="inline-block rounded-lg bg-primary-600 px-8 py-3 font-medium text-white transition-colors hover:bg-primary-700"
            >
              Login with Azure AD
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};
