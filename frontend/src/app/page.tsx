import Link from "next/link";

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-10 bg-zinc-950 text-white">
      {/* Logo */}
      <div className="w-16 h-16 rounded-2xl bg-white flex items-center justify-center">
        <svg className="w-8 h-8 text-zinc-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </div>

      {/* Title */}
      <h1 className="text-4xl font-bold text-center mt-6">
        Law Chatbot
      </h1>

      {/* Description */}
      <p className="text-zinc-400 text-center text-base max-w-md mt-4 leading-relaxed">
        Hệ thống hỏi đáp thông minh tra cứu văn bản quy phạm pháp luật Việt Nam
      </p>

      {/* Buttons */}
      <div className="flex gap-5 mt-8">
        <Link
          href="/login"
          className="px-8 py-3 bg-white text-zinc-900 font-medium rounded-full hover:bg-zinc-200 transition-colors"
        >
          Đăng nhập
        </Link>
        <Link
          href="/register"
          className="px-8 py-3 border border-zinc-700 text-white font-medium rounded-full hover:border-zinc-500 transition-colors"
        >
          Tạo tài khoản
        </Link>
      </div>

      {/* Features */}
      <div className="mt-14 grid grid-cols-1 md:grid-cols-3 gap-12 max-w-4xl text-center">
        {/* Feature 1 */}
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 rounded-xl border border-zinc-800 flex items-center justify-center">
            <svg className="w-6 h-6 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h3 className="font-semibold mt-4">Tra cứu nhanh</h3>
          <p className="text-zinc-500 text-sm mt-2">
            Tìm kiếm thông tin pháp luật chính xác trong vài giây
          </p>
        </div>

        {/* Feature 2 */}
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 rounded-xl border border-zinc-800 flex items-center justify-center">
            <svg className="w-6 h-6 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="font-semibold mt-4">Phân tích PDF</h3>
          <p className="text-zinc-500 text-sm mt-2">
            Upload tài liệu và hỏi đáp trực tiếp với nội dung
          </p>
        </div>

        {/* Feature 3 */}
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 rounded-xl border border-zinc-800 flex items-center justify-center">
            <svg className="w-6 h-6 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 className="font-semibold mt-4">Phân tích ảnh</h3>
          <p className="text-zinc-500 text-sm mt-2">
            Chụp ảnh văn bản để trích xuất và tra cứu
          </p>
        </div>
      </div>

      {/* Footer */}
      <p className="text-zinc-600 text-xs mt-10">
        © 2025 Law Chatbot. All rights reserved.
      </p>
    </div>
  );
}
