import { useState } from "react";
import { PuntoVentaForm } from "@/components/PuntoVentaForm";
import { PuntoVentaList } from "@/components/PuntoVentaList";
import { Facturador } from "@/components/Facturador";
import { Toaster } from "@/components/ui/toaster";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleSuccess = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-background font-sans antialiased p-8">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight">Facturador ARCA</h1>
        <p className="text-muted-foreground mt-2">
          Sistema de gestión de comprobantes electrónicos
        </p>
      </header>

      <main className="max-w-5xl mx-auto">
        <Tabs defaultValue="config" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-8">
            <TabsTrigger value="config">Configuración (Puntos de Venta)</TabsTrigger>
            <TabsTrigger value="facturas">Factura Electrónica</TabsTrigger>
          </TabsList>

          <TabsContent value="config">
            <div className="grid gap-8 md:grid-cols-2">
              <div>
                <PuntoVentaForm onSuccess={handleSuccess} />
              </div>
              <div>
                <PuntoVentaList refreshTrigger={refreshTrigger} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="facturas">
            <Facturador />
          </TabsContent>
        </Tabs>
      </main>
      <Toaster />
    </div>
  );
}

export default App;

