# dotnet sdk imajı çektik buil olarak adlandırdık
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build

#çalışma dizinini belirledik
WORKDIR /src

#tüm dosyaları çalışma dizinine kopyaladık
COPY . .
#gerekli bağımlılıklar csproj dosyasından alınarak yüklenir
RUN dotnet restore

#production için yayınlanabilri çıktı oluşturuluyor -c release ile
# release konfigürasyonu kullan, -o /app/publish ile bu dizne oluşan
#dosyayı koy dedik
RUN dotnet publish -c Release -o /app/publish

#çalıştırabilmek için runtime ortamı imajı çektik sdk gerek yok yalnız çalıştırma
FROM mcr.microsoft.com/dotnet/aspnet:8.0

#çalışma dizini
WORKDIR /app

#build stageindeki publish dosyasını dizine kopyaladık
COPY --from=build /app/publish .

# 8080 üstünden yayın yapma bilgisi verdik
EXPOSE 8080

#konteynır çalışırken uygulamayı çalıştırma komutu verdik 
ENTRYPOINT ["dotnet", "TodoApi.dll"]
