import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";

interface PuntoVenta {
    id: number;
    numero: number;
    cuit: string;
    es_produccion: boolean;
}

export function PuntoVentaList({ refreshTrigger }: { refreshTrigger: number }) {
    const { toast } = useToast();
    const [puntos, setPuntos] = useState<PuntoVenta[]>([]);
    const [testingConnection, setTestingConnection] = useState<number | null>(null);

    useEffect(() => {
        fetchPuntos();
    }, [refreshTrigger]);

    const fetchPuntos = async () => {
        try {
            const response = await api.get("/puntos-venta/");
            setPuntos(response.data);
        } catch (error) {
            console.error("Error fetching puntos de venta:", error);
        }
    };

    const testConnection = async (id: number) => {
        setTestingConnection(id);
        try {
            const response = await api.get(`/afip/test-connection/${id}`);
            toast({
                title: "Conexión Exitosa",
                description: `AFIP respondió OK. Último comprobante: ${response.data.ultimo_comprobante_c}`,
                duration: 5000,
                className: "bg-green-500 text-white",
            });
        } catch (error: any) {
            console.error(error);
            toast({
                title: "Error de Conexión",
                description: error.response?.data?.detail || "No se pudo conectar con AFIP",
                variant: "destructive",
            });
        } finally {
            setTestingConnection(null);
        }
    };

    return (
        <Card className="w-full max-w-4xl mx-auto mt-8">
            <CardHeader>
                <CardTitle>Puntos de Venta Configurados</CardTitle>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Número</TableHead>
                            <TableHead>CUIT</TableHead>
                            <TableHead>Entorno</TableHead>
                            <TableHead>Acciones</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {puntos.map((pv) => (
                            <TableRow key={pv.id}>
                                <TableCell className="font-medium">{pv.numero}</TableCell>
                                <TableCell>{pv.cuit}</TableCell>
                                <TableCell>
                                    <Badge variant={pv.es_produccion ? "destructive" : "secondary"}>
                                        {pv.es_produccion ? "PRODUCCIÓN" : "TESTING"}
                                    </Badge>
                                </TableCell>
                                <TableCell>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => testConnection(pv.id)}
                                        disabled={testingConnection === pv.id}
                                    >
                                        {testingConnection === pv.id ? "Probando..." : "Probar Conexión"}
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                        {puntos.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center py-4 text-muted-foreground">
                                    No hay puntos de venta configurados.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
}
