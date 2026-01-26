import { ChatInterface } from './components/ChatInterface';

function App() {
  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 md:p-8 bg-[url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop')] bg-cover bg-center bg-fixed relative">
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-0" />

      <div className="relative z-10 w-full">
        <ChatInterface />
      </div>
    </div>
  );
}

export default App;
