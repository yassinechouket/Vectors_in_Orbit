import "./globals.css";
import Header from "./components/Header";
import { UserProvider } from "@/lib/UserContext";

export const metadata = {
  title: "Matcha AI - Smart Product Discovery",
  description: "AI-powered product recommendations that understand you",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <UserProvider>
          <Header />
          <main>{children}</main>
        </UserProvider>
      </body>
    </html>
  );
}
