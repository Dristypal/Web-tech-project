import { GraduationCap, ShieldAlert, Newspaper, TrendingUp, MessageSquare, Facebook, Twitter, Instagram, Linkedin, Mail, Phone, MapPin } from 'lucide-react';
import { useNavigate } from 'react-router';

export function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#F8FAFC]" style={{ fontFamily: 'Inter, sans-serif' }}>
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-[1440px] mx-auto px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <GraduationCap className="w-8 h-8 text-[#2563EB]" />
              <span className="text-xl font-semibold text-gray-900">Campus Connect</span>
            </div>
            <div className="flex items-center gap-8">
              <a href="#" className="text-gray-700 hover:text-[#2563EB] transition-colors">Home</a>
              <a href="#" className="text-gray-700 hover:text-[#2563EB] transition-colors">News</a>
              <button 
                onClick={() => navigate('/login')}
                className="text-gray-700 hover:text-[#2563EB] transition-colors"
              >
                Login
              </button>
              <button 
                onClick={() => navigate('/login')}
                className="bg-[#2563EB] text-white px-6 py-2 rounded-xl hover:bg-[#1d4ed8] transition-colors"
              >
                Register
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-[#2563EB] to-[#1e40af] text-white">
        <div className="max-w-[1440px] mx-auto px-8 py-24">
          <div className="max-w-3xl">
            <h1 className="text-5xl font-bold mb-6 leading-tight">
              Connecting Students, Empowering Administration
            </h1>
            <p className="text-xl mb-8 text-blue-100">
              A comprehensive platform for seamless campus communication, complaint tracking, and governance. Making university life better, one connection at a time.
            </p>
            <button 
              onClick={() => navigate('/student-dashboard')}
              className="bg-white text-[#2563EB] px-8 py-3 rounded-xl hover:bg-gray-100 transition-colors text-lg font-semibold"
            >
              Get Started
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-[1440px] mx-auto px-8 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">Platform Features</h2>
          <p className="text-gray-600 text-lg">Everything you need for efficient campus management</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Feature Card 1 */}
          <div className="bg-white p-8 rounded-xl shadow-sm hover:shadow-md transition-shadow border border-gray-100">
            <div className="w-14 h-14 bg-blue-50 rounded-xl flex items-center justify-center mb-4">
              <MessageSquare className="w-7 h-7 text-[#2563EB]" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Complaint Tracking</h3>
            <p className="text-gray-600">
              Submit and track complaints with real-time status updates. Get quick resolutions for campus issues.
            </p>
          </div>

          {/* Feature Card 2 */}
          <div className="bg-white p-8 rounded-xl shadow-sm hover:shadow-md transition-shadow border border-gray-100">
            <div className="w-14 h-14 bg-blue-50 rounded-xl flex items-center justify-center mb-4">
              <Newspaper className="w-7 h-7 text-[#2563EB]" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Campus News</h3>
            <p className="text-gray-600">
              Stay updated with latest announcements, events, exams, and placement opportunities.
            </p>
          </div>

          {/* Feature Card 3 */}
          <div className="bg-white p-8 rounded-xl shadow-sm hover:shadow-md transition-shadow border border-gray-100">
            <div className="w-14 h-14 bg-blue-50 rounded-xl flex items-center justify-center mb-4">
              <ShieldAlert className="w-7 h-7 text-[#2563EB]" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Anonymous Reporting</h3>
            <p className="text-gray-600">
              Report issues anonymously with complete privacy and confidentiality protection.
            </p>
          </div>

          {/* Feature Card 4 */}
          <div className="bg-white p-8 rounded-xl shadow-sm hover:shadow-md transition-shadow border border-gray-100">
            <div className="w-14 h-14 bg-blue-50 rounded-xl flex items-center justify-center mb-4">
              <TrendingUp className="w-7 h-7 text-[#2563EB]" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Analytics Dashboard</h3>
            <p className="text-gray-600">
              Comprehensive insights and analytics for administrators to track and manage campus operations.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white mt-20">
        <div className="max-w-[1440px] mx-auto px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {/* About */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <GraduationCap className="w-7 h-7 text-[#2563EB]" />
                <span className="text-xl font-semibold">Campus Connect</span>
              </div>
              <p className="text-gray-400">
                Empowering universities with smart communication and governance solutions.
              </p>
            </div>

            {/* Contact Info */}
            <div>
              <h4 className="text-lg font-semibold mb-4">Contact Us</h4>
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-gray-400">
                  <Mail className="w-5 h-5" />
                  <span>support@campusconnect.edu</span>
                </div>
                <div className="flex items-center gap-3 text-gray-400">
                  <Phone className="w-5 h-5" />
                  <span>+1 (555) 123-4567</span>
                </div>
                <div className="flex items-center gap-3 text-gray-400">
                  <MapPin className="w-5 h-5" />
                  <span>University Campus, Building A</span>
                </div>
              </div>
            </div>

            {/* Social Icons */}
            <div>
              <h4 className="text-lg font-semibold mb-4">Follow Us</h4>
              <div className="flex gap-4">
                <a href="#" className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-[#2563EB] transition-colors">
                  <Facebook className="w-5 h-5" />
                </a>
                <a href="#" className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-[#2563EB] transition-colors">
                  <Twitter className="w-5 h-5" />
                </a>
                <a href="#" className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-[#2563EB] transition-colors">
                  <Instagram className="w-5 h-5" />
                </a>
                <a href="#" className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-[#2563EB] transition-colors">
                  <Linkedin className="w-5 h-5" />
                </a>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2026 Campus Connect. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
