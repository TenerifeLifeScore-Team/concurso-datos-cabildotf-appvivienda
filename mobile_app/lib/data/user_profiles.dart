// Archivo: lib/data/user_profiles.dart

class UserProfile {
  final String nombre;
  final String icono; // Por si luego queremos ponerle un emoji o icono al menú
  final Map<String, double> sliders;
  final List<String> checksMarcados;

  UserProfile({
    required this.nombre,
    required this.icono,
    required this.sliders,
    required this.checksMarcados,
  });
}

// Aquí iremos añadiendo todos los perfiles que haga tu compañero
final Map<String, UserProfile> perfilesPredefinidos = {
  "Estudiante Universitario": UserProfile(
    nombre: "Estudiante Universitario",
    icono: "🎓",
    sliders: {
      "Salud vital": 3.0,
      "Salud especializada": 2.0,
      "Educación": 5.0,
      "Transporte público": 5.0,
      "Cultura": 5.0,
      "Ocio, Hobbies y Tecnología": 2.0,
      "Mascotas": 0.0,
      "Centros Deportivos": 3.0,
      "Naturaleza": 0.0,
      "Camping": 0.0,
      "Alimentación y Despensa": 3.0,
      "Cuidado Personal y Salud": 1.0,
      "Hogar y Bricolaje": 0.0,
      "Moda y Shopping": 2.0,
      "Cafeterías y Mañaneo": 4.0,
      "Casual, Fast Food y Bares de Paso": 3.0,
      "Gastronomía y Guachinches": 3.0,
      "Vida Nocturna y Copas": 3.0,
      "Parques": 0.0,
    },
    checksMarcados: [
      "centro de salud",
      "farmacia",
      "servicios hospitalarios",
      "clinica dental",
      "fisioterapia rehabilitacion",
      "enseñanza universitaria",
      "Guagua",
      "Tranvia",
      "biblioteca ludoteca",
      "libreria papeleria discoteca",
      "actividades deporte ocio",
      "bazar multitienda estanco",
      "alimentacion supermercados",
      "alimentacion vinoteca",
      "peluqueria estetica",
      "perfumeria estetica complementos",
      "bisuteria complementos",
      "centro comercial",
      "centro comercial hogar moda",
      "cafeteria",
      "café",
      "bar cafeteria zumeria",
      "cibercafe",
      "autobar",
      "bar",
      "bar cafeteria",
      "bar cibercafe",
      "bar kiosco",
      "bar terraza",
      "restaurante pizzeria",
      "restaurante",
      "restaurante buffet",
      "restaurante meson",
      "bar cerveceria",
      "bar cafeteria pub",
      "barclub",
      "discoteca",
      "discoteca club",
      "pub",
      "sala de fiestas"
    ],
  ),
  
  // "Familia con Hijos": UserProfile( ... ), <-- Aquí irán los siguientes
};