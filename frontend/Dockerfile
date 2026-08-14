#node24 için alpine imajını çekiyoruz ve stage'i build oalrak adlandırıyoruz
FROM node:24-alpine AS build  

#çalışma dizinini app olarak seçiyoruz
WORKDIR /app

# package*.json dosyalarını çalışma dizinine kopyalıyoruz.
# npm install bu dosyalardaki bağımlılıkları kullanır.
# Ayrı kopyalamamızın sebebi Docker cache'inden yararlanmak.
# Kaynak kodu değişse bile package dosyaları değişmediyse
# npm install tekrar çalıştırılmaz.
COPY package*.json ./
#npm install komutu çalıştırdık ve gerekli bağımlılıkları yükledik
RUN npm install

#bulunduğumuz dizindeki tüm dosyaları(ilk nokta), çalışma dizinine(ikinci nokta) kopyalıyoruz
COPY . .

#projeyi buil ettik
RUN npm run build

#ngix için alpine imajı çektik
FROM nginx:alpine

#--from=build --> build isimli stageden dist dizinindeki dosyaları
# /usr/share/nginx/html dizninine kopyaladık
COPY --from=build /app/dist /usr/share/nginx/html

# bilgisayardaki nginx.conf dosyasını nginx stageindeki default conf dosyasına kopyalıyoruz
COPY nginx.conf /etc/nginx/conf.d/default.conf

#uygulamayı 80 portundan yayınlayacağımızı bildirdik
EXPOSE 80

#nginx komutu ile çalıştırmaay başlarken -g daemon off komutu ile arka planda çalışmasını önledik
#docker çalışabilmesi için foregroundda çalışması gerekli
CMD ["nginx", "-g", "daemon off;"]