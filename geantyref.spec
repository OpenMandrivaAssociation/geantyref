Name:		geantyref
Version:	1.3.16
Release:	1
Summary:	Generic type reflection for Java
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/leangen/geantyref
# Tag geantyref-v1.3.16. Spock 2.4 calls GenericTypeReflector and
# TypeToken from this jar. Upstream builds with Maven. This package
# compiles the main sources with javac. The Maven tool is not invoked.
Source0:	geantyref-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem

%description
io.leangen.geantyref:geantyref 1.3.16. TypeToken captures a parameterized
type such as List of String. The main sources are compiled with javac
at release 8.

%prep
%autosetup -n geantyref-%{version} -p1
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
find . -type d -name '*.jar' -print >> binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
find src/main -name '*.java' | sort > sources.list
test "$(wc -l < sources.list)" -eq 24

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p classes
javac --release 8 -Xlint:-options -d classes @sources.list
test "$(find classes -name '*.class' | wc -l)" -eq 33
for cls in \
	io.leangen.geantyref.TypeToken \
	io.leangen.geantyref.GenericTypeReflector
do
	javap -v -classpath classes "$cls" | grep -F -q 'major version: 52'
done
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: io.leangen.geantyref' > manifest.mf
jar cfm geantyref.jar manifest.mf -C classes .
jar i geantyref.jar
jar tf geantyref.jar | grep -F -q 'io/leangen/geantyref/TypeToken.class'
desc=$(jar --describe-module --file geantyref.jar)
printf '%s\n' "$desc" | grep -F -q 'io.leangen.geantyref'
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	printf '%s\n' "$desc"
	exit 1
fi

cat > geantyref.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>io.leangen.geantyref</groupId>
  <artifactId>geantyref</artifactId>
  <version>%{version}</version>
  <name>GeantyRef</name>
  <description>Generic type reflection library with support for AnnotatedType.</description>
  <url>https://github.com/leangen/geantyref</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0</url>
    </license>
  </licenses>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact geantyref.pom:geantyref.jar \
	--file-name geantyref \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/io.leangen.geantyref/geantyref.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "geantyref"' "$idx"
test -s %{buildroot}%{_javadir}/geantyref.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
JAR=%{buildroot}%{_javadir}/geantyref.jar
test -s "$JAR"
mkdir -p check
cat > check/Smoke.java << 'EOF'
import io.leangen.geantyref.TypeToken;
import java.lang.reflect.ParameterizedType;
import java.lang.reflect.Type;
import java.util.List;

public class Smoke {
    public static void main(String[] args) {
        Type type = new TypeToken<List<String>>() { }.getType();
        if (!(type instanceof ParameterizedType)) {
            throw new AssertionError(String.valueOf(type));
        }
        ParameterizedType parameterized = (ParameterizedType) type;
        Type raw = parameterized.getRawType();
        Type arg = parameterized.getActualTypeArguments()[0];
        if (raw != List.class || arg != String.class) {
            throw new AssertionError(raw + " " + arg);
        }
        System.out.println("geantyref_ok " + raw.getTypeName() + " " + arg.getTypeName());
    }
}
EOF
javac --release 8 -Xlint:-options -cp "$JAR" -d check check/Smoke.java
"$JAVA_HOME/bin/java" -cp "check:$JAR" Smoke > check/out.txt
cat check/out.txt
grep -F -qx 'geantyref_ok java.util.List java.lang.String' check/out.txt

%files -f .mfiles
%doc README.md
%license LICENSE
