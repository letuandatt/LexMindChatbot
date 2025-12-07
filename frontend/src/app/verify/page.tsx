"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function VerifyPage() {
    const searchParams = useSearchParams();
    const token = searchParams.get("token");

    const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
    const [message, setMessage] = useState("");

    useEffect(() => {
        if (!token) {
            setStatus("error");
            setMessage("Token xác thực không hợp lệ hoặc không tồn tại.");
            return;
        }

        const verifyToken = async () => {
            try {
                const res = await fetch(`${API_URL}/auth/verify?token=${token}`);
                const data = await res.json();

                if (res.ok) {
                    setStatus("success");
                    setMessage(data.message || "Tài khoản của bạn đã được xác thực thành công!");
                } else {
                    setStatus("error");
                    setMessage(data.detail || "Xác thực thất bại. Token có thể đã hết hạn.");
                }
            } catch {
                setStatus("error");
                setMessage("Đã xảy ra lỗi khi xác thực. Vui lòng thử lại sau.");
            }
        };

        verifyToken();
    }, [token]);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center px-6 py-10 bg-zinc-950 text-white">
            {/* Loading State */}
            {status === "loading" && (
                <>
                    <div className="w-16 h-16 rounded-full border-4 border-zinc-800 border-t-white animate-spin"></div>
                    <h1 className="text-2xl font-bold mt-8">Đang xác thực...</h1>
                    <p className="text-zinc-500 mt-3">Vui lòng đợi trong giây lát</p>
                </>
            )}

            {/* Success State */}
            {status === "success" && (
                <>
                    <div className="w-16 h-16 rounded-full border-2 border-green-500 flex items-center justify-center">
                        <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <h1 className="text-2xl font-bold mt-6">Xác thực thành công!</h1>
                    <p className="text-zinc-500 mt-3 text-center max-w-sm">{message}</p>
                    <Link
                        href="/login"
                        className="mt-8 px-8 py-3 bg-white text-zinc-900 font-medium rounded-full hover:bg-zinc-200 transition-colors"
                    >
                        Đăng nhập ngay
                    </Link>
                </>
            )}

            {/* Error State */}
            {status === "error" && (
                <>
                    <div className="w-16 h-16 rounded-full border-2 border-red-500 flex items-center justify-center">
                        <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </div>
                    <h1 className="text-2xl font-bold mt-6">Xác thực thất bại</h1>
                    <p className="text-zinc-500 mt-3 text-center max-w-sm">{message}</p>
                    <div className="flex gap-4 mt-8">
                        <Link
                            href="/register"
                            className="px-6 py-3 border border-zinc-700 text-white font-medium rounded-full hover:border-zinc-500 transition-colors"
                        >
                            Đăng ký lại
                        </Link>
                        <Link
                            href="/"
                            className="px-6 py-3 bg-white text-zinc-900 font-medium rounded-full hover:bg-zinc-200 transition-colors"
                        >
                            Về trang chủ
                        </Link>
                    </div>
                </>
            )}

            <p className="text-zinc-700 text-xs mt-10">© 2025 Law Chatbot. All rights reserved.</p>
        </div>
    );
}
